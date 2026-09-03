"""High-level ONE-FILE backtest runner on top of the core modules. Short, explicit, testable.

Typical use for a new engine:
    bt.backtest.sleeve(signal, returns, cost_bps=6.4) -> Series (net daily returns)
or for a full 2-leg book / EW portfolio:
    bt.backtest.book(weights, returns, ...) -> Series
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from bt.engine import lag_signal, vol_target_scale, cost_turnover, borrow_cost, margin_cost
from bt.metrics import report


def sleeve(signal: pd.Series, returns: pd.DataFrame, target: float = 0.10,
           cost_bps: float = 6.4, borrow: float = 0.005, short_frac: float = 1.0,
           max_lev: float = 1.6, margin_rate: float = 0.045) -> pd.Series:
    """One sleeve: T+1 position = lag_signal(signal) vol-targeted, net of costs+borrow+margin.
    `returns` = per-name returns aligned to signal index (col 'a' used if 1-col).
    Returns daily net return (gross exposure approx target, capped to max_lev)."""
    sig = signal.reindex(returns.index).fillna(0.0)
    pos = lag_signal(sig)
    scale = vol_target_scale(returns.iloc[:, 0]).fillna(1.0)
    w = pos * scale
    w = w.to_frame('w') if isinstance(w, pd.Series) else w
    # cap leverage on the single-name path
    from bt.engine import cap_leverage
    wc = cap_leverage(w, max_lev=max_lev)
    r = wc['w'] * returns.iloc[:, 0]
    gross = wc['w'].abs()
    net = (r - cost_turnover(wc, cost_bps)
           - borrow_cost(wc, borrow, short_frac)
           - margin_cost(gross, margin_rate, max_lev)).dropna()
    return net


def book(weights: pd.DataFrame, returns: pd.DataFrame, cost_bps: float = 6.4,
         target: float = 0.10, borrow: float = 0.005, max_lev: float = 1.6,
         margin_rate: float = 0.045) -> pd.Series:
    """A multi-leg book: given target weights (aligned to returns), apply per-name approx
    vol scaling is the caller's job; here just position = lag(weights), net of costs etc.
    NOTE: this is a lightweight runner; for precise champion construction use the dedicated
    builders. Returns net daily return series."""
    w = weights.reindex(returns.index).fillna(0.0).shift(1)
    from bt.engine import cap_leverage
    wc = cap_leverage(w, max_lev=max_lev)
    r = (wc * returns.fillna(0.0)).sum(axis=1)
    gross = wc.abs().sum(axis=1)
    net = (r - cost_turnover(wc, cost_bps)
           - borrow_cost(wc, borrow)
           - margin_cost(gross, margin_rate, max_lev)).dropna()
    return net
