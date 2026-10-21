#!/usr/bin/env python3
"""R4 bounded TRUTH20Y param identification screen (HUNT_TREASFUT).

R4 NEW FACTS vs R3:
  1. All 14 TRUTH20Y-pool inputs are now CONTENT-KNOWN (10 git-SAME vs c745682,
     3 = costfix trio already blob-swapped in R3, brwt5/7/10 untracked-but-present
     with pre-book mtimes 13:47-48 < book 16:07). The R3 story 'blobs lost' is void
     for every input — if the reconstruction still fails, it fails on CONSTRUCTION
     (params/calendar/blend), not on missing inputs.
  2. TRUTH20Y.json publishes NO A/B params. R3 assumed FINAL_TRUTH's (.072/.04,
     .093/.03). V2 (11:32/12:36, same day) documents (.090/.030, .106/.0255) and
     R4 proved that config + V2-era blobs reproduces V2 EXACTLY — so the same-day
     V2 config is a legitimate second pre-registered candidate.
This screen tests ONLY documented/pre-registered configs on the blob-pinned pool:
  P1: FINAL_TRUTH A/B (R3's choice, re-run on pinned pool as control)
  P2: V2 A/B        (pre-registered candidate)
  P3: E1 config TGT .085 THR .035 FR .4 (single-book; E1 note 'FR .4' differs)
plus a calendar check. No tuning: if none lands <=1e-12, TRUTH20Y stays quarantined
with a strengthened evidence base.
"""
import json
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6 / 10000
PRE = (f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/work_r4/pre_costfix_sleeves")

POOL_H = {
 "A5r7":     "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "A5r2":     "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7E":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxastsE": f"{PRE}/E1_QAxasts_tsmom189_2006.csv",   # pinned c745682 blob
 "dualmom":  f"{PRE}/QA_dualmom_band121.csv",          # pinned c745682 blob
 "carryv2E": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "XGB1y":    "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "A1credit": "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "C5ngE":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsumE": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "brwt15E":  f"{PRE}/E1_brwt_spread_rev15_2000.csv",  # pinned c745682 blob
 "brwt10":   "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":    "campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":    "campaign/agents/COORD/sleeves/brwt5.csv",
}
POOL_H.pop("C5ngstray", None)

OUTS = {
 "BALANCED": "GOAL100_TRUTH20Y_BALANCED_daily.csv",
 "AGGRESSIVE": "GOAL100_TRUTH20Y_AGGRESSIVE_daily.csv",
 "SAFE": "GOAL100_TRUTH20Y_SAFE_daily.csv",
}


def load(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def vt(r, tgt, min_win=60, cap=8.0):
    vol = r.rolling(min_win).std().shift(1) * np.sqrt(252)
    s = (tgt / vol).clip(upper=cap)
    s[vol.isna()] = 0
    return r * s.fillna(0), s


def construct(pool, TGT, THR, start="2006-10-01", FR=0.5, LB=126):
    V, S = {}, {}
    for n, p in pool.items():
        r = load(p)
        v, s = vt(r, 0.10)
        V[n], S[n] = v, s
    Vn = pd.DataFrame(V)
    Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1)
    blend = blend[blend.index >= start]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, _ = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * COST).dropna()


def committed(book):
    return pd.read_csv(f"{ROOT}/campaign/results/{OUTS[book]}", index_col=0,
                       parse_dates=True).iloc[:, 0].dropna()


def dev(recon, com):
    j = pd.concat([recon.rename("r"), com.rename("c")], axis=1, join="inner").dropna()
    if not len(j):
        return float("nan"), 0
    return float((j.r - j.c).abs().max()), len(j)


def main():
    com = {b: committed(b) for b in OUTS}
    print("committed calendars identical:",
          com["SAFE"].index.equals(com["AGGRESSIVE"].index) and
          com["SAFE"].index.equals(com["BALANCED"].index))
    print(f"committed n={len(com['BALANCED'])} "
          f"{com['BALANCED'].index.min().date()}..{com['BALANCED'].index.max().date()}\n")

    # P1: FINAL_TRUTH A/B on the blob-pinned pool (R3 control, now with pinned blobs)
    A1 = construct(POOL_H, 0.072, 0.040)
    B1 = construct(POOL_H, 0.093, 0.030)
    BAL1 = ((A1 + B1) / 2).dropna()
    print("P1 FINAL_TRUTH cfg (.072/.040, .093/.030) on pinned pool:")
    for book, r in [("SAFE", A1), ("AGGRESSIVE", B1), ("BALANCED", BAL1)]:
        md, n = dev(r, com[book])
        print(f"  {book:11s} maxdev {md:.4e}  n_overlap {n}/{len(com[book])}")

    # P2: V2 A/B on the same pinned pool (pre-registered same-day config)
    A2 = construct(POOL_H, 0.090, 0.030)
    B2 = construct(POOL_H, 0.106, 0.0255)
    BAL2 = ((A2 + B2) / 2).dropna()
    print("\nP2 V2 cfg (.090/.030, .106/.0255) on pinned pool:")
    for book, r in [("SAFE", A2), ("AGGRESSIVE", B2), ("BALANCED", BAL2)]:
        md, n = dev(r, com[book])
        print(f"  {book:11s} maxdev {md:.4e}  n_overlap {n}/{len(com[book])}")

    # P3: E1 cfg single book
    A3 = construct(POOL_H, 0.085, 0.035, FR=0.4)
    md, n = dev(A3, com["SAFE"])
    print(f"\nP3 E1 cfg (.085/.035 FR.4) vs SAFE: maxdev {md:.4e} n {n}")
    B3 = construct(POOL_H, 0.093, 0.030, FR=0.4)
    md, n = dev(B3, com["AGGRESSIVE"])
    print(f"P3b (.093/.030 FR.4) vs AGGRESSIVE: maxdev {md:.4e} n {n}")

    # calendar check: does committed index minus reconstructable union say anything new?
    u = None
    for p in POOL_H.values():
        s = load(p)
        idx = s.index[s.index >= pd.Timestamp("2006-10-01")]
        u = idx if u is None else u.union(idx)
    dropped = com["BALANCED"].index.difference(u)
    extra = u.difference(com["BALANCED"].index)
    print(f"\ncommitted-days NOT in sleeve union: {len(dropped)} (R3: 1 stray 2009-07-26)")
    if len(dropped):
        print("  ", list(map(str, dropped[:5].date)))
    print(f"union-days NOT in committed: {len(extra)}")
    yr = (com["BALANCED"].groupby(com["BALANCED"].index.year).apply(
        lambda s: float((1 + s).prod() - 1)) * 100)
    print(f"committed BAL yearly (pct): min {yr.min():.2f} ({yr.idxmin()}), "
          f"2006 {yr.get(2006, float('nan')):.2f}")


if __name__ == "__main__":
    main()
