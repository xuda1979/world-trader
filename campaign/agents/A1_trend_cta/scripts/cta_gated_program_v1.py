#!/usr/bin/env python3
"""A1_trend_cta round r1 — composite CTA program (NEAR-MISS, not saved as sleeve).

Book A: 7-asset L/S TSMOM on FRED macro series (xau, wti_full, brent, natgas,
        dxy-inverse, us10y-inverse, us2y-inverse), lookbacks 63/126/252 averaged,
        rb=5 sample-and-hold, per-asset 10%/7 vol target, sequential expanding book scale.
Book B: long-only trend-gated inverse-vol RP on SPX, US10Y-inverse, US2Y-inverse, XAU,
        L=252 gate, wlb=42 (shifted 1d), rb=5, 42d trailing book vol scale, RF collateral.
Composite 50/50 + expanding 10% vol scale. Costs 6bps/side on turnover.

GATES (r1): SR 0.87 PASS, halves 0.58/1.14 PASS, yearly 2 neg (>-5%) PASS,
plateau PASS, scramble p=0.061 FAIL (pre-committed <0.05). => NOT SAVED.
Status kept for reproducibility + r2 iteration base.
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A1_trend_cta")
import numpy as np, pandas as pd
from data import fred, closes, ff_factors, COST
from engine_a1 import sr, halves_sr, yearly, var_mom, positions, scale_pipeline

COST_D = COST / 1e4
OUT = "/tmp/cta_gated_program_v1.csv"

def build():
    rf = ff_factors()["RF"]
    # ----- Book A -----
    specsA = [("xau",1),("wti_full",1),("brent",1),("natgas",1),("dxy",-1),("us10y",-1),("us2y",-1)]
    lvA = pd.DataFrame({n: fred(n)[~fred(n).index.duplicated(keep="last")].sort_index() for n,_ in specsA})
    idx = pd.DatetimeIndex(sorted(set().union(*[set(lvA[c].dropna().index) for c in lvA.columns])))
    lvA = lvA.reindex(idx).ffill()
    retsA = lvA.pct_change()
    for n,fl in specsA: retsA[n] = retsA[n]*fl
    flA = pd.Series(dict(specsA))
    smA = sum(var_mom(lvA, L)*flA for L in [63,126,252])/3
    hA = positions(retsA, smA, rb=5, target=0.10)
    netA, _ = scale_pipeline(hA, retsA, target=0.10)
    netA = netA[hA.abs().sum(axis=1) > 0]
    # ----- Book B -----
    px = closes(); spx = px["SPY"].astype(float).sort_index()
    assets = {"SPX": spx, "US10Y": fred("us10y"), "US2Y": fred("us2y"), "XAU": fred("xau")}
    lvB = pd.DataFrame({k: v[~v.index.duplicated(keep="last")].sort_index() for k,v in assets.items()})
    dates = pd.DatetimeIndex(sorted(set().union(*[set(lvB[c].dropna().index) for c in lvB.columns])))
    lvB = lvB.reindex(dates).ffill()
    retsB = lvB.pct_change().loc["2008-01-01":]
    gate = (np.sign(lvB/lvB.shift(252)-1) > 0).astype(float).shift(1)
    vol = (retsB.rolling(42, min_periods=42).std()*np.sqrt(252)).shift(1)
    W = (0.10/vol).replace([np.inf,-np.inf], np.nan)
    W = W.div(W.sum(axis=1), axis=0)
    raw = W.where(gate > 0)
    held = raw.copy()
    held[np.arange(len(raw)) % 5 != 0] = np.nan
    held = held.ffill().fillna(0.0)
    gross = (held*retsB).sum(axis=1) + (1.0-held.sum(axis=1)).clip(lower=0)*rf.reindex(retsB.index).fillna(0)/252
    sd = gross.shift(1).rolling(42, min_periods=42).std()*np.sqrt(252)
    S = (0.10/sd).clip(0.2, 3.0).fillna(1.0)
    heldS = (held.T*S).T
    gross2 = (heldS*retsB).sum(axis=1) + (1.0-heldS.sum(axis=1)).clip(lower=0)*rf.reindex(retsB.index).fillna(0)/252
    netB = gross2 - heldS.diff().abs().sum(axis=1).fillna(0)*COST_D
    # ----- Composite -----
    ci = netA.index.intersection(netB.index)
    rawC = 0.5*netA[ci] + 0.5*netB[ci]
    mean=0.0; M2=0.0; cnt=0; Sprev=1.0
    out=np.zeros(len(rawC))
    for t,r in enumerate(rawC.values):
        out[t]=Sprev*r
        cnt+=1; d=r-mean; mean+=d/cnt; M2+=d*(r-mean)
        if cnt>60:
            sd=np.sqrt(M2/(cnt-1))*np.sqrt(252)
            if sd>0: Sprev=float(np.clip(0.10/sd,0.2,3.0))
    return pd.Series(out, index=rawC.index, name="ret")

if __name__ == "__main__":
    r = build()
    r.to_csv(OUT)
    h1,h2 = halves_sr(r); yr = yearly(r); neg = yr[yr<0]
    print(f"saved {OUT}: SR={sr(r):.2f} H1={h1:.2f} H2={h2:.2f} "
          f"vol={r.std()*np.sqrt(252)*100:.1f}% negYr={len(neg)} {[(int(k),round(float(v)*100,2)) for k,v in neg.items()]}")
