#!/usr/bin/env python3
"""Hypothesis L13: 13-pool rows-kept construction, new sleeves inside the vt pipeline
with per-sleeve vt 0.08 (SnP has 13 cols), then final blend of the 13 normalized series."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

ALL13 = dict(POOL11, **NEW)
NALL = len(ALL13)  # 13

def build13v2(TGT, THR, PS=0.08, REBAL='formula'):
    R13 = {n: sn_raw(p) for n, p in ALL13.items()}
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in ALL13}).dropna(how='all')
    capWP = SnP / NALL
    V = {}; S = {}
    for n in ALL13:
        v, s = vt(R13[n], PS)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC.get(n, 6.0)-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1)
    blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL == 'formula':
        reb = Sd.diff().abs().sum(axis=1)/NALL + gs.diff().abs().fillna(0)
        r_out = r_out - reb.reindex(r_out.index).fillna(0)*6e-4
    elif REBAL == 'exact':
        pos = Sd.mul(gs, axis=0).mul(sc, axis=0)
        reb = pos.diff().abs().sum(axis=1)/NALL
        r_out = r_out - reb.reindex(r_out.index).fillna(0)*6e-4
    terms = []
    for n in POOL11:
        sf = SHORTF[n]
        if sf > 0:
            terms.append(SnP[n]/NALL * sc * sf * (0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
    return r_out.dropna(how='all'), dict(Sd=Sd, gs=gs, sc=sc, SnP=SnP)

if __name__ == "__main__":
    ROOT = "/Users/daxu/software/world-trader"
    v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    for REBAL in ['formula', 'exact']:
        A, stA = build13v2(0.07, 0.04, REBAL=REBAL)
        Bp, stB = build13v2(0.091, 0.03, REBAL=REBAL)
        BAL = ((A+Bp)/2).dropna()
        print(f"REBAL={REBAL}: SAFE n={len(A)} BAL n={len(BAL)} span {BAL.index[0].date()}..{BAL.index[-1].date()}")
        for nm, cand in [("SAFE", A), ("BAL", BAL), ("AGGR", Bp)]:
            old = {"SAFE": v2s, "BAL": v2, "AGGR": v2a}[nm]
            j = pd.concat([old.rename('old'), cand.rename('new')], axis=1, join='inner').dropna()
            md = float((j.old-j.new).abs().max())
            print(f"  {nm}: overlap {len(j)} max|diff|={md:.3e}")
