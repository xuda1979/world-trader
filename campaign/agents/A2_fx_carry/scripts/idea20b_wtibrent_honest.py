"""Idea 20b (charter 5, deep dive): WTI-Brent spread z-fade — full gates + publication-lag honesty test.

VERDICT: REJECTED. Zero-lag daily z-fade looks spectacular (SR 1.97, H1 2.23/H2 1.69, 1 neg yr,
plateau across zwin 63/126/252, scramble p=0.000, corr 0.08 to library) BUT EIA daily spot prints
are published the NEXT morning; the honest decision point is t+1 => SR collapses to 0.41 (H1 0.40,
H2 0.41). Weekly decision with 2-day staleness: SR 0.41-0.49. The zero-lag P&L is earned on the
first move after a print not yet public at decision time = lookahead. Do NOT trade/save.

Also: Apr-2020 negative WTI spot (-$36.98) is treated as unpriceable (P&L zeroed) in all variants —
the unclamped zero-lag run adds a phantom +147% single day.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
import numpy as np, pandas as pd
from a2_lib import px_series
from util import cost, vol_target, gates, halves_ok, yearly, scramble_test

wti, brent = px_series("WTI"), px_series("BRENT")
idx = wti.index.union(brent.index)
w = wti.reindex(idx).ffill().astype(float)
b = brent.reindex(idx).ffill().astype(float)
bad = ((w < 5) | (b < 5)).fillna(True)          # Apr-2020 negative WTI print = unpriceable
spr = (w - b).mask(bad)
fwd = (spr.diff() / w).fillna(0.0).shift(-1)    # decision-date forward return, $-normalized
sr = lambda x: x.mean()/x.std()*np.sqrt(252) if x.std() > 0 else 0

def build(zwin=126, zthr=1.0, ef=0.75, lag=0):
    z = (spr - spr.rolling(zwin).mean()) / spr.rolling(zwin).std()
    pos = np.sign(-z).where(z.abs() > zthr, 0.0).replace(0, np.nan)
    pos = pos.where(z.abs() > zthr*ef, 0).ffill().fillna(0)
    pos = pos.shift(lag).fillna(0.0)
    pos = pos.mask(bad | bad.shift(1).fillna(True), 0.0)
    gross = (pos * fwd).dropna()
    to = pos.diff().abs().fillna(0)
    raw = (cost(gross, to) - to*6.0/1e4).dropna()   # 2 legs x 6bps one-side
    return pos, raw, vol_target(raw, 0.10).dropna()

if __name__ == "__main__":
    for lag in (0, 1, 2):
        pos, raw, r = build(lag=lag)
        g = gates(r); h1, h2 = halves_ok(r)
        print(f"lag={lag}: SR={sr(r):.2f} H1={h1:.2f} H2={h2:.2f} pass={g.get('pass_')} {g.get('why','')}")
    pos, raw, r = build(lag=0)
    j = pd.concat([pos, fwd], axis=1).dropna()
    _, p = scramble_test(j.iloc[:,0], j.iloc[:,1], n=200, seed=7)
    print(f"zero-lag scramble p={p:.3f} (correct pairing: pos vs forward return)")
