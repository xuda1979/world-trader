"""HUNT_SECTOR_FULL engine: sector-relative z-reversion books on REAL SPDR closes.

Method (extends committed near-miss sec3_sector_trio.py, same signal family):
  spread = ln(A/B); z = (spread - rolling_mean(lb)) / rolling_std(lb)
  anti-book: w_A = clip(-z/cap, -0.5, 0.5); w_B = -w_A
  T+1: positions shift(1); costs 6.4bps/side on |dw| (all legs); borrow 0.5%/yr on shorts.
No XLE/XOP (excluded by charter: oil redundant with champion).
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ROOT = '/Users/daxu/software/world-trader'
DATA = f'{ROOT}/tools/quant/data/more_etf'
TDDATA = f'{ROOT}/tools/quant/data/twelvedata'
COST_BPS = 6.4
BORROW = 0.005
ANN = 252.0

CACHE: dict = {}


def load_etf(t: str) -> pd.Series:
    """REAL close series: more_etf first (XLK etc.), twelvedata fallback (XLB/XLF/XLI)."""
    if t in CACHE:
        return CACHE[t]
    try:
        df = pd.read_csv(f'{DATA}/{t}.csv', index_col=0, parse_dates=True)
    except FileNotFoundError:
        df = pd.read_csv(f'{TDDATA}/{t}.csv', index_col=0, parse_dates=True)
    v = pd.to_numeric(df['close'], errors='coerce')
    v = v[v > 0]
    v = v[~v.index.duplicated(keep='last')].sort_index()
    v.name = t
    CACHE[t] = v
    return v


def build_weights(a: pd.Series, b: pd.Series, lb: int = 15, cap: float = 1.5) -> pd.DataFrame:
    """ANTI z-reversion weights on the 2 legs (T+1 shifted, dead when z saturates)."""
    px = pd.DataFrame({'A': a, 'B': b}).dropna()
    sp = np.log(px['A'] / px['B'])
    m = sp.rolling(lb).mean()
    s = sp.rolling(lb).std()
    z = (sp - m) / s
    w = (-z / cap).clip(-0.5, 0.5).fillna(0.0)
    pos = pd.DataFrame({'A': w, 'B': -w})
    return pos.shift(1).fillna(0.0)


def compute_costs(w: pd.DataFrame, rets: pd.DataFrame,
                  cost_bps: float = COST_BPS, borrow: float = BORROW):
    """Gross PnL, cost (6.4bps x one-side |dw| across ALL legs), borrow (0.5%/yr shorts)."""
    r = rets.reindex(w.index).fillna(0.0)
    gross = (w * r).sum(axis=1)
    turn = w.diff().abs().sum(axis=1).fillna(0.0)
    cost = turn * cost_bps / 1e4
    shorts = -w.clip(upper=0.0).sum(axis=1)
    bor = shorts * borrow / ANN
    net = gross - cost - bor
    return net, cost, bor


def mkbook(a: pd.Series, b: pd.Series, lb: int = 15, cap: float = 1.5):
    """Net daily return of one 2-leg anti z-reversion book."""
    w = build_weights(a, b, lb=lb, cap=cap)
    px = pd.DataFrame({'A': a, 'B': b}).dropna()
    rets = pd.DataFrame({'A': px['A'].pct_change(), 'B': px['B'].pct_change()})
    return compute_costs(w, rets)[0]


def ew_books(books: list) -> pd.Series:
    """Equal-weight average across books (champion convention)."""
    return pd.concat(books, axis=1).mean(axis=1)
