"""A5 idea 1: VIX term-structure contango carry. Long SPY when VIX<VIX3M (contango),
flat when backwardation. T+1, vol-target 10% (expanding trailing). 6bps/side.
Data 2009-09..2026-08 (vix3m constraint). Param scan over ratio threshold & hysteresis.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
from a5_common import *
import data as D

vd = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv', parse_dates=['DATE']).set_index('DATE')['vix']
v3 = pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv', parse_dates=['DATE']).set_index('DATE')['vix3m']
ts = pd.concat([vd, v3], axis=1).dropna()
spy = D.closes()["SPY"]
r1 = spy.pct_change()
r1.index = r1.index.tz_localize(None)

def run(th=1.0, hyst=0.0, vt=0.10):
    ratio = ts["vix"] / ts["vix3m"]
    pos = pd.Series(np.where(ratio < th, 1.0, 0.0), index=ratio.index)
    if hyst > 0:  # enter when ratio < th, exit when ratio > th + hyst
        st = 0.0; out = []
        for v in ratio.values:
            if v < th: st = 1.0
            elif v > th + hyst: st = 0.0
            out.append(st)
        pos = pd.Series(out, index=ratio.index)
    pos = pos.shift(1)                       # T+1
    to = pos.diff().abs().fillna(pos.abs())
    gross = pos * r1.reindex(pos.index).fillna(0.0)
    net = gross - to * D.COST / 1e4
    # vol target on trailing realized vol of the STRATEGY, expanding
    strat_vol = net.rolling(60).std()
    scale = (vt / np.sqrt(252) / strat_vol).clip(0, 2.0).shift(1).fillna(0.0)
    net = (net * scale)
    to2 = (pos * scale).diff().abs().fillna((pos*scale).abs())
    net = net - to2 * D.COST / 1e4
    return net.dropna()

if __name__ == "__main__":
    print("=== param scan (th, hyst) ===")
    best = None
    for th in [0.95, 0.98, 1.0, 1.02]:
        for hy in [0.0, 0.02, 0.05, 0.10]:
            n = run(th, hy)
            h1, h2 = halves(n)
            print(f"th={th} hyst={hy}: SR={sr(n):.2f} H1={h1:.2f} H2={h2:.2f} ann={stats(n)['ann']:.1f}% negyr={stats(n)['neg_yr']}")
    n = run(1.0, 0.0)
    ok, txt = gate_report("contango th=1 hyst=0", n)
    print(txt); print("ALL GATES:", ok)
    print("yearly:", {k: v for k, v in stats(n)['yearly'].items()})
