#!/usr/bin/env python3
"""RAWEW14 HOBR CANDIDATE builder/verifier (CAMP_COST R6 charter (a), adoption study).

14-sleeve PURE re-solve of rawew13v2_build: relw = max(IS_SR,0)^0.55 on the SAME IS window
(<2017-01-01), adding RB_hobr_crack_hyst_w63_z10_zo10 as a 14th slot. This is the only
construction bt/verify_champion.py can certify 7/7 - its weights_repro check recomputes
relw = max(IS_SR,0)^p from the weights CSV and the sleeve frame (tol 1e-9), so any
hand-capped or blend weight file fails weights_repro fail-closed. The charter's w<=15% NAV
cap therefore must hold as an OUTCOME of the re-solve (it does: HOBR share 1.46%..9.98%).

Construction mirrors rawew13v2_build.build() exactly: same load+dropna, same >=2008-03-31
filter, same nav.shift(1) causal NAV-drift weights row-normalized to sum K then scaled to
gross 1.6 exactly, same FULL |dW| @ 6.4bps one-side cost + 4.5%/yr margin on (1.6-1),
day-1 entry uncharged.

Usage:
  python3 work_r6/rawew14_candidate.py --verify   # pins vs committed champion (no writes)
  python3 work_r6/rawew14_candidate.py --emit     # writes results/RAWEW14_HOBR_CANDIDATE_*
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
sys.path.insert(0, ROOT + "/campaign/scripts")

import rawew13v2_build as B13  # noqa: E402

HOBR_REL = "campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv"
# ITER19 (2026-09-13): the main builder PRUNED brwt15. RAWEW14 predates that, so pin the
# historical 13-sleeve pool it was actually built on (else it silently rebuilds a
# different book and the archived-pin tests break).
_HIST_BRWT15 = "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv"
NAMES14 = B13.NAMES + ([] if "brwt15" in B13.NAMES else ["brwt15"]) + ["RB_hobr"]
PATHS14 = {**B13.PATHS, "RB_hobr": HOBR_REL, "brwt15": _HIST_BRWT15}

GEAR, RATE, BPS = B13.GEAR, B13.RATE, B13.BPS
IS_END, P, START = B13.IS_END, B13.P, "2008-03-31"

last_Wg = None  # module-global weights path of the most recent build() (test access)


def build(frame=None, hobr_relw_override=None):
    """Return (net, relw, gross, to, df). Sets module global last_Wg."""
    global last_Wg
    if frame is None:
        frame = pd.DataFrame({n: B13.load(PATHS14[n]).dropna() for n in NAMES14})
        frame = frame[frame.index >= START]
    isr = frame[frame.index < IS_END]
    SR = pd.Series({n: B13.is_sr(isr[n]) for n in frame.columns})
    relw = np.maximum(SR, 0.0) ** P
    if hobr_relw_override is not None:
        relw["RB_hobr"] = float(hobr_relw_override)
    nav = (1 + frame.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(frame.columns)
    Wg = d2 * (GEAR / len(frame.columns))
    last_Wg = Wg
    port = (frame.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=frame.index)
           - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / 252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, frame


def hobr_nav_share():
    """HOBR capital share of gross, daily (uses the last build's weights)."""
    if last_Wg is None:
        build()
    return last_Wg["RB_hobr"] / last_Wg.abs().sum(axis=1)


def stats(r):
    r = r.dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return {
        "n": int(len(r)), "start": str(r.index[0].date()), "end": str(r.index[-1].date()),
        "ann_cagr_pct": float(((1 + r).prod() ** (252 / len(r)) - 1) * 100),
        "ann_arith_pct": float(r.mean() * 252 * 100),
        "sr": float(r.mean() / r.std(ddof=1) * np.sqrt(252)),
        "mdd_pct": mdd * 100,
        "neg_years": int((yr < 0).sum()), "worst_year_pct": float(yr.min() * 100),
        "n_years": int(len(yr)),
    }


def halves_sr(r):
    mid = r.index[len(r) // 2]
    sr = lambda x: (x.mean() / x.std(ddof=1) * np.sqrt(252)) if x.std(ddof=1) > 0 else float("nan")
    return sr(r[r.index < mid]), sr(r[r.index >= mid]), mid


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--verify"
    net, relw, gross, to, df = build()
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([champ.rename("c13"), net.rename("c14")], axis=1, join="inner").dropna()
    s13, s14 = stats(j.c13), stats(j.c14)
    share = hobr_nav_share().reindex(j.index)
    d_sr = s14["sr"] - s13["sr"]
    d_ann = s14["ann_cagr_pct"] - s13["ann_cagr_pct"]
    d_mdd = s14["mdd_pct"] - s13["mdd_pct"]
    print(f"frame: n={len(df)} sleeves={len(df.columns)} "
          f"{df.index.min().date()}..{df.index.max().date()}")
    print(f"relw14: {dict(relw.round(4))}")
    print(f"HOBR NAV share: min {share.min():.5f} mean {share.mean():.5f} max {share.max():.5f} "
          f"(cap 0.15 -> {'OK' if share.max() <= 0.15 else 'BREACH'})")
    print(f"gross: mean {gross.mean():.9f} max {gross.max():.12f} days>1.6 {int((gross > 1.6 + 1e-9).sum())}")
    print(f"c13: {s13}")
    print(f"c14: {s14}")
    print(f"DELTA: dAnn {d_ann:+.4f}pp dSR {d_sr:+.4f} dMDD {d_mdd:+.4f}pp")
    h1o, h2o, mid = halves_sr(j.c13)
    h1n, h2n, _ = halves_sr(j.c14)
    print(f"halves book SR: c13 H1 {h1o:.3f} H2 {h2o:.3f} | c14 H1 {h1n:.3f} H2 {h2n:.3f} "
          f"(dH1 {h1n - h1o:+.4f} dH2 {h2n - h2o:+.4f}, split {mid.date()})")
    isc, oos = net[net.index < "2017-01-01"], net[net.index >= "2017-01-01"]
    sro = lambda x: x.mean() / x.std(ddof=1) * np.sqrt(252)
    print(f"c14 IS SR {sro(isc):.4f} (n={len(isc)}) OOS SR {sro(oos):.4f} (n={len(oos)})")
    print(f"turnover {to.mean() * 252 * BPS:.4f} bp/yr (c13: 5.2622)")
    if mode == "--emit":
        cp = f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv"
        wp = f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv"
        net.to_frame("ret").to_csv(cp)
        relw.to_frame("relw").to_csv(wp)
        print(f"EMITTED {cp} ({len(net)} rows) + {wp} ({len(relw)} rows)")


if __name__ == "__main__":
    main()
