"""Feature engineering for next-day big-move prediction.

All features at row T are computed strictly from bar data available at/just
before the close of day T (open/high/low/close/vol of days <= T). No look-ahead.
Target defined separately: return close(T) -> close(T+1).

Inputs: dict of per-field DataFrames (dates x tickers). Returns dict of feature
DataFrames (dates x tickers) with identical index/columns alignment.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def build_features(P: dict) -> dict:
    """P must contain keys close/open/high/low/vol, each a dates x tickers DataFrame,
    all sharing the same index and columns. Returns dict of feature DataFrames."""
    close, open_, high, low, vol = P["close"], P["open"], P["high"], P["low"], P["vol"]
    daily_ret = close.pct_change()

    feats = {}

    # --- momentum / reversal at multiple horizons ---
    for n in [1, 2, 3, 5, 10, 20, 60, 120]:
        feats[f"mom_{n}"] = close / close.shift(n) - 1.0

    feats["trend_250"] = close / close.shift(250) - 1.0

    # --- realized volatility ---
    for n in [5, 10, 20, 60]:
        feats[f"rvol_{n}"] = daily_ret.rolling(n).std()

    # --- scaled momentum (return / vol over window) ---
    for n in [5, 20]:
        m = (close / close.shift(n) - 1.0)
        s = daily_ret.rolling(n).std()
        feats[f"sharpe_{n}"] = m / s

    # --- RSI(14) ---
    up = daily_ret.clip(lower=0)
    dn = (-daily_ret).clip(lower=0)
    roll_up = up.rolling(14).mean()
    roll_dn = dn.rolling(14).mean()
    rs = roll_up / roll_dn.replace(0, np.nan)
    feats["rsi_14"] = 100 - 100 / (1 + rs)

    # --- price location vs moving averages ---
    for n in [5, 20, 60, 200]:
        ma = close.rolling(n).mean()
        feats[f"dist_ma{n}"] = close / ma - 1.0

    # --- intraday amplitude ---
    feats["range_pct"] = (high - low) / close
    feats["range_pct_ma10"] = feats["range_pct"].rolling(10).mean()

    # --- close location within day's range ---
    rng = (high - low).replace(0, np.nan)
    feats["close_pos"] = (close - low) / rng

    # --- overnight gap (today open vs yesterday close) ---
    feats["gap"] = open_ / close.shift(1) - 1.0

    # --- log volume + volume ratios ---
    lv = np.log(vol + 1.0)
    feats["logvol"] = lv
    for n in [5, 20, 60]:
        feats[f"vol_ratio_{n}"] = lv / lv.rolling(n).mean()

    # --- interaction: today's return x today's volume ratio (strong + on high vol) ---
    feats["ret_x_volratio"] = daily_ret * feats["vol_ratio_20"]

    # --- recent extreme: has the stock just had a big up day? (autocorrelation of tails) ---
    feats["bigup_prev1"] = (daily_ret >= 0.05).astype(float)
    feats["bigup_prev5"] = (daily_ret >= 0.05).rolling(5).sum()

    return feats


def to_xy(feats: dict, target: pd.DataFrame,
          start=None, end=None, drop_na=True):
    """Flatten the panel into an (X, y) matrix for a classifier.
    target: dates x tickers DataFrame of NEXT-day returns (row T = realized over T->T+1).
    Returns X (n x p float), y (n int 0/1), and metadata arrays for reflattening."""
    names = sorted(feats.keys())
    X_parts = {k: feats[k] for k in names}
    # stack all features & target into long frames
    idx = target.index
    cols = target.columns

    # only keep rows within [start, end]
    if start is not None:
        idx = idx[idx >= start]
    if end is not None:
        idx = idx[idx <= end]

    # Build long DataFrames
    frames = []
    for k in names:
        f = feats[k].loc[idx, cols]
        s = f.stack().rename(k)
        frames.append(s)
    X = pd.concat(frames, axis=1)

    y_series = target.loc[idx, cols].stack().rename("retnext")
    y = (y_series >= 0.05).astype(int).to_numpy()
    retnext = y_series.to_numpy()

    # metadata: date and ticker for each row (for walk-forward / grouping)
    meta = pd.DataFrame({"date": y_series.index.get_level_values(0),
                         "ticker": y_series.index.get_level_values(1)})
    return X, y, retnext, meta, names
