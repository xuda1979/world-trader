#!/usr/bin/env python3
"""CFX4 robustness battery with CORRECT per-book aggregation: scrub-k, epjack63, LOYO,
start cuts, block-boot pA. Compare to HUNT_CARRYFX claims (scrub50 +0.61, epjackMin +1.68,
LOYO-min +1.573, 2025+ 0.426, block-boot pA 0.0000)."""
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
sigd, mvd = {}, {}
for a, b in books:
    spl = np.log(C[a])-np.log(C[b])
    zz = [(spl-spl.rolling(lb).mean())/spl.rolling(lb).std() for lb in (21,63)]
    z = sum(zz)/2
    sigd[(a,b)] = (((2.0*(-z)).clip(-2,2)/2).shift(1)).dropna()
    mvd[(a,b)] = R[a]-R[b]
def book_net(s, k):
    a, b = k
    return (s*mvd[k].reindex(s.index) - 2*s.diff().abs()*COST - 0.005/252*s.abs())
tot = sum(book_net(sigd[k], k) for k in books).dropna()
def sr(x): return float(x.mean()/x.std()*np.sqrt(252)) if x.std() > 0 else np.nan
print(f"rebuilt SR {sr(tot):.4f} n={len(tot)}")
def scrub(r, k):
    v = r.values.copy(); o = np.argsort(v)[::-1]; v[o[:k]] = np.nan
    return sr(pd.Series(v, index=r.index).dropna())
print("scrub-k:", {k: round(scrub(tot,k),3) for k in [5,10,20,50]})
n = len(tot); w = 63; mins = []
for i0 in range(0, n-w, w):
    mask = np.ones(n, bool); mask[i0:i0+w] = False
    mins.append(sr(tot.iloc[mask]))
print(f"epjack63: min {min(mins):.3f} over {len(mins)} windows")
loyo = {int(y): round(sr(tot[tot.index.year != y]),3) for y in sorted(set(tot.index.year))}
print("LOYO:", loyo, "min", min(loyo.values()))
for y0 in [2020,2021,2022,2023,2024,2025]:
    s = tot[tot.index.year >= y0]
    print(f"start {y0}+: SR {sr(s):.3f} n={len(s)}")
# block-boot pA
def boot_pA(r, B=10, nperm=1000, seed=0):
    x = r.values; nn = len(x); nb = nn//B
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, nn-B, size=(nperm, nb))
    cnt = 0
    for row in starts:
        xb = np.concatenate([x[s:s+B] for s in row])[:nn]
        if xb.std() > 0 and xb.mean()/xb.std()*np.sqrt(252) <= 0: cnt += 1
    return cnt/nperm
print("block-boot pA (1000x):", [round(boot_pA(tot,10,1000,s),4) for s in range(3)])
