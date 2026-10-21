#!/usr/bin/env python3
"""GOAL100 CHAMPION20Y_V2 — canonical build script (v1.0, frozen 2026-09-01).

Regenerates the 20.6-year champion (2006-10-02..2026-08-28) from 13 committed sleeve files:
  campaign/results/GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv   (headline: 50/50 A+B)
  campaign/results/GOAL100_CHAMPION20Y_V2_SAFE_daily.csv       (A)
  campaign/results/GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv (B)

Pool (13): 12-sleeve E1 de-truncated pool (natgas 1998+, brwt 2000+, bond2y 1992+,
GLD-proxy panels 2006-07; see campaign/agents/E1_20yspan/FINDINGS.md) + MHX
(multi-horizon walk-forward XGB, enters 2008-09 — dilutive before that, conservative).

Construction: identical to champion_build.py (per-sleeve vt10 rolling-60d shift-1 cap8,
plain EW, global vt, 126d DD throttle shift-1, 6bps on turnover) with:
  A: TGT=0.090 THR=0.030 FR=0.5 LB=126, start 2006-10-01
  B: TGT=0.106 THR=0.0255 FR=0.5 LB=126, start 2006-10-01
  BALANCED = 0.5*(A+B).

Stats (committed): ann 65.1%, SR 6.17 (monthly 3.83, CI [3.39,4.35]), MaxDD -7.2%,
1/21 neg years (2006 -1.6%), OOS17+ 71.5% @ -7.2%. Cost stress: 10bps => 64.4%/-7.5%.
Drop-B3 variant: 64.8%/-7.8% (B3 optional, disclosed).

Usage: python3 campaign/scripts/champion20y_build.py [--verify]
"""
import sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
COST = 6 / 10000

POOL20 = {
 "A5r7":    "campaign/agents/A5_vol_cond/sleeves/A5_r7_credit_composite.csv",
 "a6r7":    "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "A1inf":   "campaign/agents/E1_20yspan/sleeves/E1_A1inf_GLD_2006.csv",
 "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "A1credit":"campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv",
 "XGB1y":   "campaign/results/sleeve_library/XGB1y_deploy.csv",
 "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "brwt":    "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "B3momhml":"campaign/agents/B3_antiregime/ref_momhml_composite.csv",
 "C5ng":    "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "MHX":     "campaign/agents/COORD/sleeves/MHX_multihorizon_xgb.csv",
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

def construct(pool, TGT, THR, start, FR=0.5, LB=126):
    V, S = {}, {}
    for n, p in pool.items():
        r = load(p); v, s = vt(r, 0.10); V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= start]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, _ = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1); tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * sc; dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * COST).dropna()

def main(verify=False):
    A = construct(POOL20, 0.090, 0.030, "2006-10-01")
    B = construct(POOL20, 0.106, 0.0255, "2006-10-01")
    BAL = ((A + B) / 2).dropna()
    outs = {
        "GOAL100_CHAMPION20Y_V2_BALANCED_daily.csv": BAL,
        "GOAL100_CHAMPION20Y_V2_SAFE_daily.csv": A,
        "GOAL100_CHAMPION20Y_V2_AGGRESSIVE_daily.csv": B,
    }
    for fn, r in outs.items():
        path = f"{ROOT}/campaign/results/{fn}"
        old = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
        md = float((j.old - j.new).abs().max())
        if verify:
            print(f"{fn}: max|new-old| = {md:.3e}  {'IDENTICAL' if md < 1e-12 else 'DIFF'}")
        else:
            r.to_frame("ret").to_csv(path)
            print(f"wrote {path} n={len(r)}")

if __name__ == "__main__":
    main(verify="--verify" in sys.argv)
