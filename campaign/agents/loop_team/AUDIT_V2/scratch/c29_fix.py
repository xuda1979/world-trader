#!/usr/bin/env python3
"""CORRECT CFX4 pos-lag scramble: per-book pnl = sig_i*mv_i - 2*|d sig_i|*COST - borrow;
circular-lag each book's sig vs ITS OWN mv (same lag all books, and per-book variants),
sum books, SR of aggregate. p(SR_lag >= SR_real)."""
import numpy as np, pandas as pd
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
sigd = {}; mvd = {}
for a, b in books:
    spl = np.log(C[a])-np.log(C[b])
    zz = [(spl-spl.rolling(lb).mean())/spl.rolling(lb).std() for lb in (21,63)]
    z = sum(zz)/2
    sigd[(a,b)] = (((2.0*(-z)).clip(-2,2)/2).shift(1)).dropna()
    mvd[(a,b)] = (R[a]-R[b])
idx = sigd[books[0]].index
for k in books[1:]: idx = idx.intersection(sigd[k].index)
def book_net(s, k):
    a, b = k
    return (s*mvd[k].reindex(s.index) - 2*s.diff().abs()*COST - 0.005/252*s.abs())
nets_real = [book_net(sigd[k], k) for k in books]
real = sum(nets_real).dropna()
sr_real = real.mean()/real.std()*np.sqrt(252)
print(f"rebuilt NET CFX4 SR: {sr_real:.4f} n={len(real)} (committed 1.9106)")

def poslag(nperm, seed, same_lag=True, lo=21):
    T = len(idx); rng = np.random.default_rng(seed); cnt = 0
    for _ in range(nperm):
        lags = rng.integers(lo, T-21, size=1 if same_lag else 4)
        tot = None
        for j, k in enumerate(books):
            lag = int(lags[0] if same_lag else lags[j])
            s = pd.Series(np.roll(sigd[k].values, lag), index=sigd[k].index)
            n = book_net(s, k)
            tot = n if tot is None else tot + n
        r = tot.dropna(); sr = r.mean()/r.std()*np.sqrt(252)
        if sr >= sr_real: cnt += 1
    return cnt/nperm
print(f"NET pos-lag same-lag 300x seed1: {poslag(300,1):.4f}")
print(f"NET pos-lag same-lag 300x seed2: {poslag(300,2):.4f}")
print(f"NET pos-lag per-book 300x:       {poslag(300,3,same_lag=False):.4f}")
print(f"NET pos-lag lags>=63 200x:       {poslag(200,4,lo=63):.4f}")
