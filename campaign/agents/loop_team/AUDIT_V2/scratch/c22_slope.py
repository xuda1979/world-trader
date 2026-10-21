#!/usr/bin/env python3
"""Robust slope of V2 vs FIX on a scan of alphas; hunt the -5.8bp fed-row value in FIX-era terms.
Also: check whether V2 == FIX recomputed at slightly different PS/TGT (e.g. per-sleeve vt 0.075?)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL
ROOT = "/Users/daxu/software/world-trader"

def sn(p):
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

R11 = {n: sn(p) for n, p in POOL11.items()}
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

dies_raw = load(NEW['diescrack']); cfx_raw = load(NEW['CFX4'])
dies = dies_raw[dies_raw.index.dayofweek < 5]
cfx = cfx_raw[cfx_raw.index.dayofweek < 5]

def build(TGT, THR, PS, SMEAR=True):
    R = R11
    if not SMEAR:
        R = {n: (lambda s: s)(None) or None for n in R11}
        R = {n: (v2lib_sn_raw(POOL11[n])) for n in R11}
    SnP = pd.DataFrame({n: vt(R[n], PS)[1] for n in POOL11}).dropna(how='all')
    capWP = SnP/11
    V = {}; S = {}
    for n in POOL11:
        v, s = vt(R[n], PS)
        V[n] = v - capWP[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs()*0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1+b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r = b - (tw.reindex(b.index).fillna(0)+dsc.fillna(0))*6e-4
    reb = Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)
    r = r - reb.reindex(r.index).fillna(0)*6e-4
    terms = [SnP[n]/11*sc*SHORTF[n]*(0.005+(0.03 if n=='dualmom' else 0.0)*0.2) for n in POOL11 if SHORTF[n]>0]
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r = r - htb.reindex(r.index).fillna(0)/252
    return r.dropna(how='all'), dict(Sd=Sd, gs=gs, sc=sc)

def v2lib_sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

# scan alphas on the smear calendar
best = None
for PS in [0.08]:
    for TGT in [0.07, 0.091]:
        pass
# slope scan
import numpy.linalg as la
common = v2.index.intersection(fix.index)
j = pd.DataFrame({'v2': v2, 'fix': fix}).loc[common].dropna()
diesx = dies.reindex(j.index).fillna(0.0); cfxx = cfx.reindex(j.index).fillna(0.0)
X = np.column_stack([j.fix, diesx, cfxx, np.ones(len(j))])
for alpha in [0.0, 1e-6, 1e-5, 1e-4]:
    coef, *_ = la.lstsq(X + 0, j.v2.values, rcond=None)
    break
coef, res, rank, sv = la.lstsq(X, j.v2.values, rcond=None)
r = j.v2.values - X@coef
print(f"slope fit: fix {coef[0]:.6f} dies {coef[1]:.6f} cfx {coef[2]:.6f} const {coef[3]:.2e} resid rms {np.sqrt((r**2).mean()):.3e}")
# per-year slope
for y in [2008, 2015, 2021, 2026]:
    m = j.index.year == y
    Xy = np.column_stack([j.fix[m], diesx[m], cfxx[m], np.ones(m.sum())])
    cy, *_ = la.lstsq(Xy, j.v2.values[m], rcond=None)
    ry = j.v2.values[m] - Xy@cy
    print(f"  {y}: fix {cy[0]:.5f} dies {cy[1]:.5f} cfx {cy[2]:.5f} resid-rms {np.sqrt((ry**2).mean()):.2e} n={m.sum()}")
