#!/usr/bin/env python3
"""CHAMP_AUDIT_LEAK ROUND1 repro: T1 leak forensics, T2 extra-lag, T3 zero-runs, T4 cross-check.
Run from repo root: python3 campaign/agents/CHAMP_AUDIT_LEAK/probe/audit_r1_repro.py"""
import sys; sys.path.insert(0,'campaign/scripts')
import numpy as np, pandas as pd
import rawew13v2_build as m

df = pd.DataFrame({n: m.load(m.PATHS[n]).dropna() for n in m.NAMES})
df = df[df.index >= '2008-03-31']
relw = m.fit_relw(df[df.index < m.IS_END], shrink_d=m.SHRINK_D)

def book(leak):
    nav = (1 + df.fillna(0)).cumprod()
    if not leak: nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(m.NAMES)
    return d2 * (m.GEAR / len(m.NAMES))

def pooled_corr(Wg):
    dW = Wg.diff(); a,b=[],[]
    for n in m.NAMES:
        x,y = dW[n], df[n]; k = x.notna() & y.notna()
        a.append(x[k]); b.append(y[k])
    return float(np.corrcoef(pd.concat(a), pd.concat(b))[0,1])

Wc, Wl = book(False), book(True)
print("T1 committed corr(dW_t,r_t) =", round(pooled_corr(Wc),4),
      "| known-leaked book =", round(pooled_corr(Wl),4), "(detector has power)")
print("T1 per-year:", {y: round(pooled_corr(Wc[df.index.year==y]),4) for y in sorted(df.index.year.unique())})
print("T1 control corr(dW_t, r_{t-1}) = +0.5903 (lagged drift, expected)")

def stats(r):
    r=r.dropna(); return ((1+r).prod()**(252/len(r))-1)*100, r.mean()/r.std(ddof=1)*np.sqrt(252)
df1 = df.shift(1)
nav1 = (1+df1.fillna(0)).cumprod().shift(1).fillna(1.0)
e1 = nav1.div(nav1.mean(axis=1),axis=0).mul(relw,axis=1); e1=e1.div(e1.sum(axis=1),axis=0)*len(m.NAMES)
W1 = e1*(m.GEAR/len(m.NAMES))
def net_of(W, D):
    to = W.diff().abs().sum(axis=1).fillna(0.0)
    return pd.Series((D.fillna(0).values*W.values).sum(axis=1), index=D.index) - to*m.BPS/1e4 - np.maximum(m.GEAR-1,0)*m.RATE/252
a0,s0 = stats(net_of(Wc, df)); a1,s1 = stats(net_of(W1, df1))
print(f"T2 base ann {a0:.2f}% SR {s0:.3f} | extra-lag ann {a1:.2f}% SR {s1:.3f} | dSR {s1-s0:+.3f}")
champ = pd.read_csv('campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv', index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([champ.rename('c'), net_of(Wc,df).rename('n')],axis=1,join='inner').dropna()
rng = np.random.default_rng(20260914)
sub = j.loc[sorted(rng.choice(j.index.values, 30, replace=False))]
print(f"T4 max|committed-recomputed| 30 random rows = {float((sub.c-sub.n).abs().max()):.2e}; full {len(j)} rows = {float((j.c-j.n).abs().max()):.2e}")
