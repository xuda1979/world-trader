#!/usr/bin/env python3
"""Last big sweep: my no-smear 13-sleeve slot build, but scan a few remaining conventions:
- new sleeves inside Vn (13-pool, per-sleeve vt) with slot-weighted mean, blend on 13 rows,
  smear vs no-smear, tw with 13-sleeve W, and borrow on 13 terms.
- ALSO: r_out dropna only where ALL NaN (already), or v2 could keep 2006-10-02 start.
Scan TGT pairs and SLOT in {0.10/12.2, 0.0455}. Print best max|diff| per config."""
import numpy as np, pandas as pd, sys, itertools, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL
ROOT = "/Users/daxu/software/world-trader"

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

v2  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

def build(TGT, THR, SLOT, smear, PS=0.08):
    ALL13 = dict(POOL11, **NEW)
    R13 = {n: sn(p, smear) for n, p in ALL13.items()}
    idx = pd.concat(R13.values(), axis=1).dropna(how='all').index
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in ALL13}).reindex(idx)
    capWP = SnP/13
    V = {}; S = {}
    for n in ALL13:
        v, s = vt(R13[n], PS)
        V[n] = v.reindex(idx) - capWP[n].diff().abs().fillna(0)*((EXEC.get(n,6.0)-6.0)/1e4)
        S[n] = s.reindex(idx)
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    wv = pd.Series({**{n:1.0 for n in POOL11}, **{n:SLOT for n in NEW}})
    W = SnP.mul(wv).div(SnP.mul(wv).sum(axis=1), axis=0).fillna(0)
    blend = Vn.mul(wv).sum(axis=1)/(11+2*SLOT)
    blend = blend[blend.index >= '2006-10-01']
    tw = ((W-W.shift(1)).abs()*0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r = b - (tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    reb = Sd.mul(wv).diff().abs().sum(axis=1)/(11+2*SLOT) + gs.diff().abs().fillna(0)
    r = r - reb.reindex(r.index).fillna(0)*6e-4
    terms = [SnP[n]*wv[n]/(11+2*SLOT)*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0)*0.2)
             for n in POOL11 if SHORTF[n]>0]
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r = r - htb.reindex(r.index).fillna(0)/252
    return r.dropna(how='all')

res = []
for smear in [True, False]:
    for SLOT in [0.10/12.2, 0.0455]:
        for exact in [0.07]:
            A = build(0.07, 0.04, SLOT, smear)
            j = pd.concat([v2.rename('o'), A.rename('n')], axis=1, join='inner').dropna()
            res.append((smear, SLOT, float((j.o-j.n).abs().max()), len(j)))
for smear, slot, md, n in res:
    print(f"smear={smear} SLOT={slot:.5f}: SAFE max|d|={md:.3e} n={n}")
