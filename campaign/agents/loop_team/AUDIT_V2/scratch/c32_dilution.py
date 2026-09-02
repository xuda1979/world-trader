#!/usr/bin/env python3
"""AUDIT_V2 check 6: slot-weight sweep 0..0.5 on my reconstruction (SAFE+BAL+AGGR).
Confirm 0.10 ~ diversification optimum; confirm no weight lifts SR_d>=5 or ann>=80 at DD<=7."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]
ALL13 = dict(POOL11, **NEW)

def build(TGT, THR, SLOT, PS=0.08):
    R13 = {n: sn_raw(p) for n, p in ALL13.items()}
    idx = pd.concat(R13.values(), axis=1).dropna(how='all').index
    wv = pd.Series({**{n: 1.0 for n in POOL11}, **{n: SLOT for n in NEW}})
    NSUM = 11 + 2*SLOT
    Vn = pd.DataFrame({n: vt(R13[n], PS)[0].reindex(idx) for n in ALL13})
    Sd = pd.DataFrame({n: vt(R13[n], PS)[1].reindex(idx) for n in ALL13})
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1].reindex(idx) for n in ALL13})
    capWP = SnP/11
    V = {}
    for n in POOL11:
        v, s = vt(R13[n], PS)
        V[n] = v.reindex(idx) - capWP[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    for n in NEW:
        V[n] = Vn[n]
    Vn2 = pd.DataFrame(V)
    blend = (Vn2*wv).sum(axis=1)/NSUM
    blend = blend[blend.index >= '2006-10-01']
    tw = None
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r = b - dsc.fillna(0)*6e-4
    reb = (Sd.mul(wv, axis=1)).diff().abs().sum(axis=1)/NSUM + gs.diff().abs().fillna(0)
    r = r - reb.reindex(r.index).fillna(0)*6e-4
    terms = [SnP[n]/11*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0)*0.2) for n in POOL11 if SHORTF[n]>0]
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r = r - htb.reindex(r.index).fillna(0)/252
    return r.dropna(how='all')

def stats(r):
    r = r.dropna()
    srd = r.mean()/r.std()*np.sqrt(252)
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12)
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()
    ann = eq.iloc[-1]**(252/len(r))-1
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    return srd, srm, mdd*100, ann*100, int((yr<0).sum())

print(f"{'SLOT':>6} | {'SR_d':>6} {'SR_m':>6} {'MDD%':>6} {'ann%':>6} {'neg':>4}  (BAL)")
rows = []
for slot in [0.0, 0.02, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
    A = build(0.07, 0.04, slot)
    Bp = build(0.091, 0.03, slot)
    BAL = ((A+Bp)/2).dropna()
    srd, srm, mdd, ann, neg = stats(BAL)
    rows.append((slot, srd, srm, mdd, ann, neg))
    print(f"{slot:>6.3f} | {srd:>6.3f} {srm:>6.3f} {mdd:>6.2f} {ann:>6.2f} {neg:>4}")
best = max(rows, key=lambda x: x[1])
print(f"\nmax SR_d at SLOT={best[0]:.3f} (SR_d {best[1]:.3f})")
print("any weight with SR_d>=5?", any(r[1] >= 5 for r in rows))
print("any weight with ann>=80 and MDD<=7?", any(r[4] >= 80 and r[3] >= -7 for r in rows))
