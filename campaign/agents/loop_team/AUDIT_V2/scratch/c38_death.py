#!/usr/bin/env python3
"""Final provenance attempt (small): scan FIX-builder param space cheaply on the SMEAR
calendar with new sleeves as SEPARATE POOL (13) and final blend by capital slot weights
where FIX engines are renormalized: r = (11/12.2)*rFIX(1.0 slots) + (0.1/12.2)*(dies+cfx) —
already tried. Instead scan: maybe V2 used per-sleeve vt 0.10 (L16-style)? Or THR/FR variants?
Grid on my 13-pool smear build: PS in {0.08, 0.10}, REBAL in {formula, exact}."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL

def sn(p, smear=True):
    r = load(p).dropna()
    if smear:
        keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
        out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
        for i in range(len(r)):
            cu += v[i]
            if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
        return out.iloc[:ki]
    return r[r.index.dayofweek < 5]

v2s = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

def build(TGT, THR, SLOT, PS, smear=True):
    ALL = dict(POOL11, **NEW)
    R13 = {n: sn(p, smear) for n, p in ALL.items()}
    idx = pd.concat(R13.values(), axis=1).dropna(how='all').index
    wv = pd.Series({**{n: 1.0 for n in POOL11}, **{n: SLOT for n in NEW}})
    NSUM = 11 + 2*SLOT
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in ALL}).reindex(idx)
    capWP = pd.DataFrame({n: vt(sn(POOL11[n], smear), PS)[1] for n in POOL11}).dropna(how='all')/11
    V = {}; Sd = {}
    for n in ALL:
        v, s = vt(R13[n], PS)
        if n in POOL11:
            v = v - capWP[n].diff().abs().reindex(idx).fillna(0)*((EXEC[n]-6.0)/1e4)
        V[n] = v.reindex(idx); Sd[n] = s.reindex(idx)
    Vn = pd.DataFrame(V); Sdd = pd.DataFrame(Sd)
    blend = (Vn*wv).sum(axis=1)/NSUM
    blend = blend[blend.index >= '2006-10-01']
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r = b - (dsc.fillna(0))*6e-4
    reb = Sdd.mul(wv, axis=1).diff().abs().sum(axis=1)/NSUM + gs.diff().abs().fillna(0)
    r = r - reb.reindex(r.index).fillna(0)*6e-4
    terms = [SnP[n]/11*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0)*0.2) for n in POOL11 if SHORTF[n]>0]
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r = r - htb.reindex(r.index).fillna(0)/252
    return r.dropna(how='all')

best = (1e9, None)
for PS in [0.08, 0.10]:
    for SLOT in [0.10/12.2, 0.0455, 0.05]:
        for smear in [True, False]:
            A = build(0.07, 0.04, SLOT, PS, smear)
            j = pd.concat([v2s.rename('o'), A.rename('n')], axis=1, join='inner').dropna()
            md = float((j.o-j.n).abs().max())
            if md < best[0]: best = (md, (PS, SLOT, smear))
            print(f"PS={PS} SLOT={SLOT:.5f} smear={smear}: SAFE max|d|={md:.3e} n={len(j)}")
print(f"\nBEST: {best}")
