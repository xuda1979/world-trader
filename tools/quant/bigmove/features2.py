"""Enhanced feature engineering for next-day big-move prediction.

Adds stock-volnormalized and market-relative features to the base set.
All at row T use only bars <= T. No look-ahead.
Every returned feature is a DataFrame (dates x tickers) with the same index/columns.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from features import build_features


def _tile(s: pd.Series, cols) -> pd.DataFrame:
    """Broadcast a date-indexed Series to a DataFrame with the given columns."""
    return pd.DataFrame({c: s for c in cols}, index=s.index)


def build_features2(P: dict) -> dict:
    close, high, low = P["close"], P["high"], P["low"]
    f = build_features(P)   # base features
    daily_ret = close.pct_change()

    # ---- equal-weight market (cross-sectional mean of daily returns per day) ----
    mkt = daily_ret.mean(axis=1, skipna=True)   # series over dates

    # market-relative daily return (stock - market), broadcast to panel
    rel = daily_ret.sub(mkt, axis=0)
    f["rel_ret_1"] = rel

    # market-relative momentum over n days
    mkt_level = close.mean(axis=1)
    for n in [5, 20]:
        stock_mom = close / close.shift(n) - 1.0
        mkt_mom = (mkt_level / mkt_level.shift(n) - 1.0)
        f[f"rel_mom_{n}"] = stock_mom.sub(mkt_mom, axis=0)

    # ---- long-run per-stock vol for normalization (rolling 250d) ----
    lr_std = daily_ret.rolling(250).std()
    for n in [1, 3, 5, 10]:
        f[f"normmom_{n}"] = (close / close.shift(n) - 1.0) / lr_std

    # ---- stock's own historical frequency of >=5% next-day moves ----
    big = (daily_ret >= 0.05).astype(float)
    f["histbig_freq_250"] = big.rolling(250).mean()
    f["histbig_freq_60"] = big.rolling(60).mean()

    # ---- recent absolute momentum ----
    for n in [5, 10]:
        f[f"absret_ma{n}"] = daily_ret.abs().rolling(n).mean()

    # ---- distance from 5d high / low; breakout proximity ----
    roll_hi5 = close.rolling(5).max()
    roll_lo5 = close.rolling(5).min()
    f["dist_hi5"] = close / roll_hi5 - 1.0
    f["dist_lo5"] = close / roll_lo5 - 1.0
    hi20 = close.rolling(20).max()
    f["close_vs_hi20"] = close / hi20 - 1.0

    # ---- interaction: big recent move + volume ratio ----
    f["bigret_prev1"] = (daily_ret.abs() >= 0.03).astype(float)
    f["big_norm_vol"] = f["bigret_prev1"] * f["vol_ratio_20"]

    # ---- market big-move day (broadcast) ----
    f["mkt_abs_ret"] = _tile(mkt.abs(), close.columns)
    f["mkt_ret"] = _tile(mkt, close.columns)

    return f
