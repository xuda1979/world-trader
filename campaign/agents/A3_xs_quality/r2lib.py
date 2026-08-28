"""r2 helpers: weight-based backtester identical in honesty mechanics to engine.py,
plus momentum feature builders. PIT: all inputs at t use data <= t; weights apply T+1."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, vol_target, strategy_ret, full_gates, COST

def wbacktest(W_me, rets):
    """W_me: DataFrame (daily idx) with target weights set at month-end rows (signal t).
    Holds until next month-end; T+1 via pos+1; cost = 6bps * one-side turnover."""
    idx = rets.index
    Wm = W_me.reindex(idx).fillna(0.0)
    mes = [d for d in month_ends(rets) if d in idx]
    w = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    prev = pd.Series(0.0, index=rets.columns)
    turn = pd.Series(0.0, index=idx)
    pos_of = {d: idx.get_loc(d) for d in mes}
    for i, t in enumerate(mes):
        neww = Wm.loc[t]
        p = pos_of[t]
        if p + 1 < len(idx):
            turn.iloc[p + 1] = 0.5 * (neww - prev).abs().sum()
            nxt_p = pos_of[mes[i + 1]] + 1 if i + 1 < len(mes) else len(idx)
            w.iloc[p + 1: nxt_p] = neww.values
            prev = neww
    gross = (w * rets.fillna(0.0)).sum(axis=1)
    return gross - turn * COST / 1e4, w, turn

def gross_lev(W):
    return W.abs().sum(axis=1)

def equal_w(scores, rets, nl_frac=1/3, ns_frac=1/3, longs_only=False):
    """Build month-end equal-weight target matrix from score panel (engine-equivalent)."""
    idx = rets.index
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    mes = [d for d in month_ends(rets) if d in idx and d in scores.index]
    for t in mes:
        row = scores.loc[t].dropna()
        if len(row) < 10: continue
        row = row.sort_values()
        n = len(row)
        nl = max(int(np.floor(n * nl_frac)), 1)
        ns = max(int(np.floor(n * ns_frac)), 1)
        for s in row.index[-nl:]: W.loc[t, s] = 1.0 / nl
        if not longs_only:
            for s in row.index[:ns]: W.loc[t, s] -= 1.0 / ns
    return W

def run_gates(W, rets, name, start=None, verbose=True):
    net, w, turn = wbacktest(W, rets)
    if start is None:
        nz = w.abs().sum(axis=1)
        start = nz[nz > 0].index[0]
    r = strategy_ret(net, start)
    ok, g = full_gates(r, name, verbose=verbose)
    return ok, g, r, net
