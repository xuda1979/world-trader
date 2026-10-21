#!/usr/bin/env python3
"""AUDIT_V2 check 5: capital-real gross leverage on my slot-weight reconstruction.
gross_t = sum_i slot_i*|scale_i(t)|*gs_t*sc_t / (11+2*SLOT). Report mean/p95/max full span
and 2008+, yearly means, days >2x disclosed mean (6.90x)."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL

def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

ALL13 = dict(POOL11, **NEW)
SLOT = 0.10; NSUM = 11 + 2*SLOT

def leverage(TGT, THR, PS=0.08):
    R13 = {n: sn_raw(p) for n, p in ALL13.items()}
    idx = pd.concat(R13.values(), axis=1).dropna(how='all').index
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in ALL13}).reindex(idx)
    wv = pd.Series({**{n: 1.0 for n in POOL11}, **{n: SLOT for n in NEW}})
    Vn = pd.DataFrame({n: vt(R13[n], PS)[0].reindex(idx) for n in ALL13})
    Sd = pd.DataFrame({n: vt(R13[n], PS)[1].reindex(idx) for n in ALL13})
    blend = (Vn*wv).sum(axis=1)/NSUM
    blend = blend[blend.index >= '2006-10-01']
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
    grossA = (Sd.abs().mul(wv, axis=1)).sum(axis=1)/NSUM * gs * sc
    grossB = ((Sd.mul(wv, axis=1)).abs().sum(axis=1))/NSUM * gs * sc
    return grossA, dict(gs=gs, sc=sc)

gA, _ = leverage(0.07, 0.04)
gB, _ = leverage(0.091, 0.03)
# V2 BAL = (SAFE+AGGR)/2 -> gross leveraged average of the two (half exposure each)
gBAL = (gA + gB)/2
def rep(g, name):
    g = g.dropna()
    g08 = g[g.index >= '2008-03-31']
    print(f"{name}: full-span mean {g.mean():.3f}x p95 {g.quantile(0.95):.3f}x max {g.max():.3f}x | 2008+ mean {g08.mean():.3f}x p95 {g08.quantile(0.95):.3f}x max {g08.max():.3f}x")
    yr = g08.groupby(g08.index.year).mean()
    print("  yearly means (2008+):", {int(k): round(v,2) for k,v in yr.items()})
    print(f"  days > 2x mean (>{2*g08.mean():.2f}x): {(g08 > 2*g08.mean()).sum()} of {len(g08)} ({(g08>2*g08.mean()).mean()*100:.1f}%)")
    print(f"  days > 1.6x: {(g08>1.6).mean()*100:.1f}%")
rep(gA, "SAFE recon"); rep(gB, "AGGR recon"); rep(gBAL, "BAL recon")
print(f"\nclaim: mean 3.45x / p95 7.18x / max 10.75x")
print(f"my BAL 2008+: mean {gBAL[gBAL.index>='2008-03-31'].mean():.3f}x; full {gBAL.mean():.3f}x")
