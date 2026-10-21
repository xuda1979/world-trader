#!/usr/bin/env python3
"""CFX4 pos-lag on the NET engine (costs change the pnl scale): permute sig vs net engine pnl
rebuild (sig*(mv) - costs), i.e. rebuild the whole net book under each circular lag.
Also scrub-k and epjack quickly to reproduce the battery claims."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
FXD = "/Users/daxu/software/world-trader/tools/quant/data/fx"
COST = 6.0/1e4
pairs = ["GBP_USD","NZD_USD","AUD_USD","EUR_USD"]
def loadf(p):
    df = pd.read_csv(f"{FXD}/{p}.csv", index_col=0, parse_dates=True)
    df = df[df.index.dayofweek < 5]; df = df[~df.index.duplicated(keep='last')].sort_index()
    return df
C = pd.DataFrame({p: loadf(p).close for p in pairs}).dropna()
R = C.pct_change()
books = [("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
sig_books = []
for a, b in books:
    spl = np.log(C[a])-np.log(C[b])
    zz = [(spl-spl.rolling(lb).mean())/spl.rolling(lb).std() for lb in (21,63)]
    z = sum(zz)/2
    sig_books.append(((2.0*(-z)).clip(-2,2)/2).shift(1))
sig = pd.concat(sig_books, axis=1).mean(axis=1)
mv = pd.concat([(R[a]-R[b]) for a,b in books], axis=1).mean(axis=1)
def net_of(s):
    n = s*mv - 2*s.diff().abs()*COST - 0.005/252*s.abs()
    return n.dropna()
base = net_of(sig.dropna())
real = base.mean()/base.std()*np.sqrt(252)
print(f"rebuilt NET CFX4 SR: {real:.4f} n={len(base)} (committed 1.9106)")

def net_poslag(nperm, seed, lo=21, hi=None):
    s0 = sig.dropna(); T = len(s0); hi = hi or T-21
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(nperm):
        lag = int(rng.integers(lo, hi))
        sp = pd.Series(np.roll(s0.values, lag), index=s0.index)
        n = net_of(sp)
        sr = n.mean()/n.std()*np.sqrt(252)
        if sr >= real: cnt += 1
    return cnt/nperm
print(f"NET pos-lag 300x seed1: {net_poslag(300,1):.4f}")
print(f"NET pos-lag 300x seed2: {net_poslag(300,2):.4f}")

# scrub-k battery
def sr(x): return x.mean()/x.std()*np.sqrt(252)
def scrub(r, k):
    v = r.values.copy(); o = np.argsort(v)[::-1]; v[o[:k]] = np.nan
    s = pd.Series(v, index=r.index).dropna()
    return sr(s)
for k in [5,10,20,50]:
    print(f"scrub{k}: {scrub(base,k):.3f}")
# episode jackknife 63d
idx = base.index; n = len(base); w = 63
mins = []
for i0 in range(0, n-w, w):
    mask = np.ones(n, bool); mask[i0:i0+w] = False
    s = base.iloc[mask]
    mins.append(sr(s))
print(f"epjack63 min SR: {min(mins):.3f} ({len(mins)} windows)")
# LOYO
loyo = {}
for y in sorted(set(base.index.year)):
    loyo[y] = sr(base[base.index.year != y])
print("LOYO:", {k: round(v,3) for k,v in loyo.items()})
# start cuts
for y0 in [2020,2021,2022,2023,2024,2025]:
    s = base[base.index.year >= y0]
    print(f"start {y0}+: SR {sr(s):.3f} n={len(s)}")
