"""Betting-Against-Beta (Frazzini-Pedersen style) on the 298-name panel.
Monthly: beta = 252d rolling vs FF market; long low-beta half / short high-beta
half (rank-weighted), gross 1.0; vol-target 10% expanding. T+1, 6bps/side."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
from data import closes, ff_factors, save_sleeve
from util import gates, cost
import numpy as np
import pandas as pd

OUT = "/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/bab.csv"

def build():
    px = closes()
    ret = px.pct_change(fill_method=None)
    ff = ff_factors()
    mkt = (ff["Mkt-RF"] + ff["RF"]).reindex(ret.index).ffill()
    var = mkt.rolling(252, min_periods=120).var()
    # rolling beta per name (loop is fine: 298 names)
    betas = {}
    for c in ret.columns:
        betas[c] = ret[c].rolling(252, min_periods=120).cov(mkt) / var
    betas = pd.DataFrame(betas)

    # monthly decision dates = last trading day of month
    mend = pd.to_datetime(pd.Series(ret.index).groupby(ret.index.to_period("M")).max().values)
    b_m = betas.reindex(mend).dropna(how="all")
    med = b_m.median(axis=1)
    w = pd.DataFrame(0.0, index=b_m.index, columns=b_m.columns)
    for t in b_m.index:
        row = b_m.loc[t].dropna()
        if len(row) < 100: continue
        k = len(row)//2
        lows = row.nsmallest(k).index; highs = row.nlargest(k).index
        # rank-weight each side
        wl = pd.Series(1.0, index=lows); wl = wl/wl.sum()
        wh = pd.Series(1.0, index=highs); wh = wh/wh.sum()
        w.loc[t, lows] = wl.values * 0.5
        w.loc[t, highs] = -wh.values * 0.5
    # daily: shift(1) => decision at t, earn t->t+1. reindex daily + ffill
    pos_d = w.reindex(ret.index).ffill()
    pos_exec = pos_d.shift(1).fillna(0.0)
    pnl = (pos_exec * ret).sum(axis=1, min_count=1)
    to = pos_exec.diff().abs().sum(axis=1).fillna(0)
    r_net = cost(pnl, to)
    vol = r_net.expanding(min_periods=126).std().shift(1)*np.sqrt(252)
    lev = (0.10/vol).clip(0, 3).fillna(0)
    return (r_net*lev).dropna()

if __name__ == "__main__":
    r = build()
    r = r[r.index >= "2008-01-01"]
    g = gates(r)
    print("BAB:", g)
    save_sleeve(r, OUT, "BAB: monthly, 252d beta, low-beta long/high short, gross1, vt10, 6bps")
