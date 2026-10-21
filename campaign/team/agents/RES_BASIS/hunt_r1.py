"""RES_BASIS R1 hunt library — cross-commodity basis engines on FRED daily spots (no browser).

All production conventions mirror campaign/scripts/HUNT_CREDIT2_round5.py (the
GATES_CONTRACT_V2 §0-accepted pattern): T+1 via shift(1), trailing-only stats (shift(1)),
vol-target via bt.engine.vol_target_scale on the gross path, 6.4bps FULL |dW| one-side
(bt.engine.cost_turnover), 0.5%/yr borrow on shorts, and the V2 battery with r = PER-UNIT
(spread) returns and sig = effective leg weight so sig*r == held gross book.
"""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT = "/Users/daxu/software/world-trader"
VT_TARGET, VT_CAP = 0.08, 3.0


def load_series(path, col=None):
    s = pd.read_csv(path, index_col=0, parse_dates=True)
    s = s[col].astype(float) if col and col in s.columns else s.iloc[:, 0].astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()


def hysteresis_state(z, z_in=2.0, z_out=0.5):
    """Band filter on shifted z: enter +1 when z>z_in (short spread later sign applied by
    caller), -1 when z<-z_in, exit when |z|<z_out; NaN z holds state, never enters."""
    st = np.zeros(len(z))
    cur = 0.0
    for i, zv in enumerate(z.values):
        if not np.isfinite(zv):
            st[i] = cur
        elif cur == 0.0:
            if zv > z_in:
                cur = 1.0
            elif zv < -z_in:
                cur = -1.0
            st[i] = cur
        elif cur == 1.0 and zv < z_out:
            cur = 0.0
            st[i] = cur
        elif cur == -1.0 and zv > -z_out:
            cur = 0.0
            st[i] = cur
        else:
            st[i] = cur
    return pd.Series(st, index=z.index)


def zscore_trailing(px_or_spread, win=40, shift_stats=True):
    """z of level vs trailing mean/sd. shift_stats=True => both stats lag 1 (decision at t
    sees only closes <= t-1: no same-day leak)."""
    m = px_or_spread.rolling(win, min_periods=win // 2).mean()
    s = px_or_spread.rolling(win, min_periods=win // 2).std()
    if shift_stats:
        m, s = m.shift(1), s.shift(1)
    z = (px_or_spread - m) / s.replace(0, np.nan)
    return z.where(s.notna())


def weekly_pub_safe(wk, lag_days=7, end=None):
    """Daily view of a weekly series under publication lag: an obs dated v becomes visible
    on v+lag_days and holds until the next obs appears. Days before the FIRST visibility
    stay NaN (never backward-fill an unpublished obs)."""
    wk = wk.sort_index()
    vis = wk.copy()
    vis.index = vis.index + pd.Timedelta(days=lag_days)
    tgt = pd.date_range(wk.index[0], end or vis.index[-1])
    daily = vis.reindex(vis.index.union(tgt)).sort_index().ffill()
    return daily.reindex(tgt)


def pair_book(r_a, r_b, spread, win, z_in, z_out, vt=True, side='meanrev',
              target=VT_TARGET, return_rpu=False):
    """Dollar-neutral 2-leg spread book on z of `spread` (trailing stats shifted 1).

    meanrev: spread rich (z>+z_in) => short A / long B, holds until |z|<z_out;
             spread cheap (z<-z_in) => long A / short B.
    mom    : position FOLLOWS the entry-state sign (spread breaking down => ride it).
    rpu = r_a - r_b (simple-return spread), so sig(=We['a']) * rpu == gross book exactly
    (V2 §0 battery convention, HUNT_CREDIT2_round5-pinned)."""
    z = zscore_trailing(spread, win=win)
    idx = z.dropna().index
    st = hysteresis_state(z.reindex(idx), z_in=z_in, z_out=z_out)
    W = pd.DataFrame(0.0, index=idx, columns=['a', 'b'])
    if side == 'meanrev':
        W['a'], W['b'] = -st, st
    elif side == 'mom':
        W['a'], W['b'] = st, -st
    else:
        raise ValueError(f"unknown side {side!r}")
    r_a = r_a.reindex(idx).fillna(0.0)
    r_b = r_b.reindex(idx).fillna(0.0)
    rpu = (r_a - r_b).rename('rpu')
    net, We, gross_r = net_of(W, pd.concat({'a': r_a, 'b': r_b}, axis=1), vt=vt, target=target)
    if return_rpu:
        return net, We, gross_r, rpu
    return net, We, gross_r


def net_of(W, R, vt=True, target=VT_TARGET):
    """T+1 effective weights, trailing vt on gross, 6.4bps full |dW| + 0.5%/yr borrow."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R.fillna(0.0)).sum(axis=1)
    if vt:
        s = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    port = (We * R.fillna(0.0)).sum(axis=1)
    cost = cost_turnover(We, cost_bps=6.4)
    borr = borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross
