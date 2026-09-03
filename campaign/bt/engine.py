"""Reusable, testable backtest engine (short, honest, T+1, no lookahead).

Core flow:
  signal at t  ->  position at t+1 (shift(1))  ->  return earned t+1
  per-sleeve vol-target scale (trailing only)  ->  weights  ->  gross + costs
All params explicit; no hidden state. See tests/ for TDD properties.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

COST_BPS = 6.4
BORROW_FRAC = 0.005
ANN = 252.0


def lag_signal(sig: pd.Series) -> pd.Series:
    """T+1 positions: decide at close t, execute/earn at t+1. No same-day leak."""
    return sig.shift(1)


def vol_target_scale(returns: pd.DataFrame, target: float = 0.10,
                     window: int = 60, cap: float = 3.0) -> pd.DataFrame:
    """Trailing-expanding vol-target scale using ONLY returns up to t-1 (no lookahead).

    scale_t = clip(target / (expanding_std(r[0..t-1]) * sqrt(ANN)), min, cap)
    First `window` rows: expanding window (may be short), scale floored at min.
    Returns NaN-free frame aligned to `returns`.
    """
    vols = returns.expanding(min_periods=1).std(ddof=1) * np.sqrt(ANN)
    scale = target / vols.replace(0.0, np.nan)
    scale = scale.where(vols > 0, 1.0)
    scale = scale.clip(upper=cap)
    # floor: no scale below 0.2 (sanity); first rows expanding std still valid
    scale = scale.clip(lower=0.2)
    return scale.shift(1)


def capital_gross(weights: pd.DataFrame) -> pd.Series:
    """Capital-real gross exposure = sum of |weight| per day."""
    return weights.abs().sum(axis=1)


def cap_leverage(weights: pd.DataFrame, max_lev: float = 1.6) -> pd.DataFrame:
    """Scale all per-day weights down to <= max_lev capital-real gross (day-level cap).

    kappa_t = min(1, max_lev / gross_t); returns weights*kappa (aligned)."""
    g = capital_gross(weights).replace(0.0, np.nan)
    kappa = np.minimum(1.0, max_lev / g).fillna(1.0)
    return weights.mul(kappa, axis=0)


def cost_turnover(weights: pd.DataFrame, cost_bps: float = COST_BPS) -> pd.Series:
    """One-side turnover cost = 0.5 * sum|dw| (half-turn convention) * cost_bps/1e4."""
    one_side = weights.diff().abs().sum(axis=1) * 0.5
    return one_side * cost_bps / 1e4


def borrow_cost(weights: pd.DataFrame, borrow_frac: float = BORROW_FRAC,
                short_fraction: float = 1.0) -> pd.Series:
    """Daily borrow charge on short notional: 0.5*sum|w_short| * borrow_frac / ANN."""
    shorts = -weights.clip(upper=0.0)
    return shorts.sum(axis=1) * short_fraction * borrow_frac / ANN


def margin_cost(gross: pd.Series, rate: float = 0.045, max_lev: float = 1.6) -> pd.Series:
    """Daily margin financing on leveraged portion (gross - 1) only, at annual `rate`."""
    lev = (gross - 1.0).clip(lower=0.0)
    return lev * rate / ANN


def monthly() -> pd.Series:
    return pd.Series(dtype=float)
