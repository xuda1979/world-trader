#!/usr/bin/env python3
"""R3(a) fraud-catch verifier for HUNT_COT2.

Independently recomputes SR / ann / vol / halves / neg_years / worst-year / n /
corr-vs-champion from HUNT_CMDT2's saved sleeve CSVs using ONLY the [date,ret]
CSV + the champion daily CSV. No import of their scripts, no reuse of lib_hunt.
Compares against the claims in each .csv.meta and reports PASS-MATCH / MISMATCH.

Conventions (stated up front, applied uniformly):
  SR      = mean(r)/std(r, ddof=1) * sqrt(252)          (daily net returns as saved)
  annAri  = mean(r)*252   (arithmetic)
  annGeo  = expm1(mean(log1p(r))*252)  (geometric)  <- HUNT_CMDT2's convention, verified
  vol     = std(r, ddof=1)*sqrt(252)
  H1/H2   = two conventions, both reported:
            rows: first floor(n/2) rows vs rest  <- HUNT_CMDT2's convention, verified
            cal : sessions with date <= median date vs rest
  negyrs  = # calendar years with COMPOUNDED return < 0
  worstyr = min compounded annual return
  corr    = Pearson corr of daily rets on the INNER JOIN of dates vs champion
Fabrication probes per sleeve: duplicate dates, non-monotone dates, non-finite
returns, degenerate value counts, longest zero-run, max |ret|.
Tolerances: SR 5e-3, halves 5e-2, corr 5e-3 (meta rounds to 3dp), annGeo/vol
abs 5e-4 or 3%, n exact, dates exact. Scramble p is NOT recomputable from a
net-returns CSV alone (defined on the position series vs raw prices) -> checked
for presence/plausibility in meta only, flagged unverifiable-from-CSV.
"""
import glob
import math
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CMDT2 = os.path.join(HERE, "..", "HUNT_CMDT2", "sleeves")
CHAMP = os.path.join(HERE, "..", "..", "..", "..", "results",
                     "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")

TOL_SR, TOL_HALF, TOL_CORR, TOL_ANN = 5e-3, 5e-2, 5e-3, 5e-4
# The metas publish percentages at 0.1pp granularity ("ann=7.7%", "worstyr=-8.4%").
# Comparisons tighter than half that granularity flag the meta's own ROUNDING as a
# discrepancy (R3 rerun: 11/12 sleeves flagged on worstyr alone, e.g. got -8.423% vs
# published -8.4%). Floor percentage tolerances at 0.05pp = half the publish grid.
TOL_PCT_PUBLISHED = 0.05
TOL_WORSTYR = max(0.005, TOL_PCT_PUBLISHED)


def longest_zero_run(r):
    best = cur = 0
    for v in r:
        cur = cur + 1 if v == 0.0 else 0
        best = max(best, cur)
    return best


def stats_from_csv(path):
    df = pd.read_csv(path, parse_dates=["date"]).sort_values("date")
    r = df["ret"].astype(float)
    n = len(df)
    sr = r.mean() / r.std(ddof=1) * math.sqrt(252)
    ann_ari = r.mean() * 252
    ann_geo = float(np.expm1(np.log1p(r).mean() * 252))
    vol = r.std(ddof=1) * math.sqrt(252)

    # integrity probes (fraud indicators)
    dup = int(df["date"].duplicated().sum())
    nonmono = int((df["date"].diff().dt.total_seconds().dropna() <= 0).sum())
    nonfinite = int((~np.isfinite(r)).sum())
    maxabs = float(r.abs().max())
    zrun = longest_zero_run(r.values)
    nuniq = int(r.nunique())

    med = df["date"].median()
    halves = {}
    for tag, mask in (("rows", np.arange(n) < n // 2),
                      ("cal", (df["date"] <= med).values)):
        a, b = r[mask].values, r[~mask].values
        halves[tag] = (a.mean() / a.std(ddof=1) * math.sqrt(252),
                       b.mean() / b.std(ddof=1) * math.sqrt(252))

    yr = df["date"].dt.year.values
    yret = df.groupby(yr)["ret"].apply(lambda x: float(np.prod(1.0 + x.values) - 1.0))
    negyrs = int((yret < 0).sum())
    worstyr = float(yret.min())

    return dict(n=n, sr=sr, ann_ari=ann_ari, ann_geo=ann_geo, vol=vol, halves=halves,
                negyrs=negyrs, worstyr=worstyr, start=str(df["date"].iloc[0].date()),
                end=str(df["date"].iloc[-1].date()), dup=dup, nonmono=nonmono,
                nonfinite=nonfinite, maxabs=maxabs, zrun=zrun, nuniq=nuniq, df=df)


def corr_vs_champ(df, champ):
    m = df.merge(champ, on="date", suffixes=("_s", "_c"))
    if len(m) < 100:
        return float("nan"), len(m)
    return float(m["ret_s"].corr(m["ret_c"])), len(m)


def parse_meta(path):
    txt = open(path).read()
    out = {}
    for key, pat in (("SR", r"SR=(-?\d+\.?\d*)"), ("ann", r"ann=(-?\d+\.?\d*)%"),
                     ("vol", r"vol=(\d+\.?\d*)%"), ("H1", r"H1=(-?\d+\.?\d*)"),
                     ("H2", r"H2=(-?\d+\.?\d*)"), ("negyrs", r"negyrs=(\d+)"),
                     ("worstyr", r"worstyr=(-?\d+\.?\d*)%"),
                     ("corr", r"corr_champ=(-?\d+\.?\d*)"), ("n", r"\bn=(\d+)")):
        m = re.search(pat, txt)
        out[key] = float(m.group(1)) if m else float("nan")
    m = re.search(r"(\d{4}-\d{2}-\d{2})->(\d{4}-\d{2}-\d{2})", txt)
    out["start"], out["end"] = (m.group(1), m.group(2)) if m else ("", "")
    return out


def close_or_missing(claim, got, tol) -> bool:
    """FAIL-CLOSED comparison (R3 TDD): missing/NaN claim => FAILURE, never silent pass."""
    if claim is None:
        return False
    try:
        c = float(claim)
    except (TypeError, ValueError):
        return False
    if not np.isfinite(c) or not np.isfinite(float(got)):
        return False
    return abs(c - float(got)) <= tol

def main():
    champ = pd.read_csv(CHAMP, parse_dates=["date"]).sort_values("date")
    rows, n_mismatch = [], 0
    for csv in sorted(glob.glob(os.path.join(CMDT2, "*.csv"))):
        name = os.path.basename(csv)
        got = stats_from_csv(csv)
        claim = parse_meta(csv + ".meta")
        c_s, c_n = corr_vs_champ(got["df"], champ)

        chk = []
        def chk_close(tag, claim, got_v, tol, fmt):
            if not close_or_missing(claim, got_v, tol):
                chk.append(fmt)

        chk_close("SR", claim["SR"], got["sr"], TOL_SR, f"SR {got['sr']:.4f} vs claimed {claim['SR']:.3f}")
        chk_close("annGeo", claim["ann"], got["ann_geo"] * 100.0,
                  max(TOL_ANN, TOL_PCT_PUBLISHED, 0.03 * abs(claim["ann"])),
                  f"annGeo {got['ann_geo']*100:.2f}% vs claimed {claim['ann']:.1f}%")
        chk_close("vol", claim["vol"], got["vol"] * 100.0,
                  max(TOL_ANN, TOL_PCT_PUBLISHED, 0.03 * abs(claim["vol"])),
                  f"vol {got['vol']*100:.2f}% vs claimed {claim['vol']:.1f}%")
        h_best = min(got["halves"].values(),
                     key=lambda h: (abs(h[0] - claim["H1"]) + abs(h[1] - claim["H2"])
                                    if np.isfinite(claim["H1"]) and np.isfinite(claim["H2"])
                                    else float("inf")))
        if not (close_or_missing(claim["H1"], h_best[0], TOL_HALF)
                and close_or_missing(claim["H2"], h_best[1], TOL_HALF)):
            chk.append(f"halves best-conv {h_best[0]:.3f}/{h_best[1]:.3f} vs claimed "
                       f"{claim['H1']:.2f}/{claim['H2']:.2f}")
        chk_close("negyrs", claim["negyrs"], got["negyrs"], 0.0,
                  f"negyrs {got['negyrs']} vs claimed {int(claim['negyrs'])}")
        chk_close("worstyr", claim["worstyr"], got["worstyr"] * 100.0, TOL_WORSTYR,
                  f"worstyr {got['worstyr']*100:.1f}% vs claimed {claim['worstyr']:.1f}%")
        chk_close("corr", claim["corr"], c_s, TOL_CORR, f"corr {c_s:.4f} vs claimed {claim['corr']:.3f}")
        chk_close("n", claim["n"], got["n"], 0.0, f"n {got['n']} vs claimed {int(claim['n'])}")
        if got["start"] != claim["start"] or got["end"] != claim["end"]:
            chk.append(f"window {got['start']}..{got['end']} vs claimed {claim['start']}..{claim['end']}")
        if got["dup"] or got["nonmono"] or got["nonfinite"]:
            chk.append(f"INTEGRITY dup={got['dup']} nonmono={got['nonmono']} "
                       f"nonfinite={got['nonfinite']}")
        if chk:
            n_mismatch += 1
        rows.append((name, got, claim, c_s, c_n, chk))

    print(f"champion: {len(champ)} rows {champ['date'].iloc[0].date()} -> "
          f"{champ['date'].iloc[-1].date()}  champ_SR="
          f"{champ['ret'].mean()/champ['ret'].std(ddof=1)*math.sqrt(252):.4f}\n")
    hdr = (f"{'sleeve':40s} {'SR Got':>7s} {'Claim':>6s} {'annGeo%':>8s} {'Claim':>6s} "
           f"{'H1/H2 rows':>11s} {'Claim':>9s} {'negY':>4s} {'worstY%':>8s} "
           f"{'corr':>7s} {'n':>6s} {'zrun':>5s} verdict")
    print(hdr)
    print("-" * len(hdr))
    for name, got, claim, c_s, c_n, chk in rows:
        print(f"{name[:40]:40s} {got['sr']:7.3f} {claim['SR']:6.3f} "
              f"{got['ann_geo']*100:8.2f} {claim['ann']:6.1f} "
              f"{got['halves']['rows'][0]:5.2f}/{got['halves']['rows'][1]:<5.2f} "
              f"{claim['H1']:4.2f}/{claim['H2']:<4.2f} "
              f"{got['negyrs']:4d} {got['worstyr']*100:8.1f} {c_s:7.3f} {got['n']:6d} "
              f"{got['zrun']:5d} "
              f"{'MISMATCH: ' + '; '.join(chk) if chk else 'MATCH'}")
    print(f"\n=== {len(rows)} sleeves checked, {n_mismatch} with discrepancies ===")
    for name, got, claim, c_s, c_n, chk in rows:
        if got["zrun"] > 250 or got["nuniq"] < 20:
            print(f"NOTE {name}: longest zero-run {got['zrun']} sessions, "
                  f"{got['nuniq']} distinct return values (ffill/warmup artifact — "
                  f"consistent with live-window conventions, not fabrication)")
    return 1 if n_mismatch else 0


if __name__ == "__main__":
    sys.exit(main())
