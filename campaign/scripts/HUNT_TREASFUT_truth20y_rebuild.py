#!/usr/bin/env python3
"""HUNT_TREASFUT round 3(a) — GOAL100_TRUTH20Y reconstruction attempt (2026-09-07).

Charter: AUDIT_CHAMP2 flagged campaign/results/GOAL100_TRUTH20Y* as untracked with the
builder absent from the tree. This script is the *attempted* reconstruction from the
described mechanism (G4_detrun/FINDINGS.md span claim + GOAL100_FINAL_TRUTH.json configs),
NOT a verified builder. Pass criterion per charter: max|recon - committed| <= 1e-12 on all
3 books. Otherwise the files stay quarantined.

Mechanism evidence used (all in-tree):
  - campaign/scripts/champion20y_build.py  (same-day ancestor, 13-pool, frozen construction:
    per-sleeve vt10 r.rolling(60).std().shift(1) cap8, NaN-skipping EW, global vt(TGT),
    126d trailing-DD throttle FR .5 shift-1, 6bps on 0.5*sum|dW| + 0.5*|dsc|, dropna)
  - campaign/results/GOAL100_FINAL_TRUTH.json (15:32, 35min before TRUTH20Y 16:07): same
    14-name pool NON-E + configs A = vt.072/thr.04, B = vt.093/thr.03, BAL = 0.5*(A+B)
  - TRUTH20Y json note: "audit-passing sleeves + E1 de-truncated variants (corr 0.98-1.0
    to audited originals); A1inf/H21/MHX/B3/A5r4 excluded; NYSE calendar"
    -> pool = FINAL_TRUTH names with the 6 non-E members swapped for E1_20yspan sleeves.
    All 14 map to files that DO exist on disk (AUDIT_CHAMP2's "pool files missing" searched
    for the literal names a6r7E/QAxastsE/... which are labels, not filenames).

Honest deviations tested below (each a plausible reading of the description):
  v_straight: construct() verbatim from champion20y_build.py with the 14-pool mapping.
Any residual mismatch is reported as exact max-dev; NO fudge knobs are tuned to close it.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6 / 10000

POOL_H = {
 "A5r7":     "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "A5r2":     "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7E":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxastsE": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "dualmom":  "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2E": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "XGB1y":    "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "A1credit": "campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "C5ngE":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsumE": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "brwt15E":  "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":   "campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":    "campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":    "campaign/agents/COORD/sleeves/brwt5.csv",
}
OUTS = {
 "BALANCED":   "GOAL100_TRUTH20Y_BALANCED_daily.csv",
 "AGGRESSIVE": "GOAL100_TRUTH20Y_AGGRESSIVE_daily.csv",
 "SAFE":       "GOAL100_TRUTH20Y_SAFE_daily.csv",
}


def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
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


def main():
    A = construct(POOL_H, 0.072, 0.040)   # SAFE  per FINAL_TRUTH.json
    B = construct(POOL_H, 0.093, 0.030)   # AGGRESSIVE per FINAL_TRUTH.json
    recon = {"SAFE": A, "AGGRESSIVE": B, "BALANCED": ((A + B) / 2).dropna()}

    print(f"{'book':12s} {'n_rec':>6s} {'n_com':>6s} {'maxdev':>12s}  span_rec")
    worst = 0.0
    for book, fn in OUTS.items():
        com = pd.read_csv(f"{ROOT}/campaign/results/{fn}", index_col=0,
                          parse_dates=True).iloc[:, 0].dropna()
        r = recon[book]
        j = pd.concat([r.rename("rec"), com.rename("com")], axis=1, join="inner").dropna()
        md = float((j.rec - j.com).abs().max()) if len(j) else float("nan")
        worst = max(worst, md if md == md else 0.0)
        flag = "REPRODUCED" if (len(j) == len(com) == len(r) and md <= 1e-12) else "MISMATCH"
        print(f"{book:12s} {len(r):6d} {len(com):6d} {md:12.4e}  "
              f"{r.index.min().date()}..{r.index.max().date()}  {flag}")

    # json 'bal' block cross-check on the reconstruction (its own conventions: arith ann)
    import json
    bal = json.load(open(f"{ROOT}/campaign/results/GOAL100_TRUTH20Y.json"))["bal"]
    r = recon["BALANCED"]
    print(f"\nrecon BAL: arith ann {r.mean()*252*100:.4f}% (json {bal['ann']}), "
          f"SR {r.mean()/r.std()*np.sqrt(252):.4f} (json {bal['sr']})")
    print(f"VERDICT: {'REPRODUCED <=1e-12' if worst <= 1e-12 else 'NOT REPRODUCED — quarantine stands'}")
    return 0 if worst <= 1e-12 else 1


if __name__ == "__main__":
    sys.exit(main())
