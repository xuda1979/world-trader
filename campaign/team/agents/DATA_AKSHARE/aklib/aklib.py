"""aklib.py — DATA_AKSHARE helpers: normalize akshare frames, fail-closed lint, manifest.

Canonical output per series: one CSV (date,open,high,low,close,volume[,open_interest]) or
(date,<field>) for non-OHLC series; lint is fail-closed (span/price/gap), matching the
team contract in campaign/team/docs/ORG.md. Data-only; no backtests.
"""
import pandas as pd

CN_OHLC = {"日期": "date", "开盘价": "open", "最高价": "high",
           "最低价": "low", "收盘价": "close", "成交量": "volume", "持仓量": "open_interest"}
EN_OHLC = ["date", "open", "high", "low", "close", "volume", "open_interest"]


def normalize(df):
    """Map Chinese/English akshare columns to canonical english names, date->YYYY-MM-DD."""
    df = df.rename(columns={k: v for k, v in CN_OHLC.items() if k in df.columns})
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df[[c for c in EN_OHLC if c in df.columns] +
              [c for c in df.columns if c not in EN_OHLC]]


def lint(df, min_span_days=365, max_gap_days=30, price_cols=("close",)):
    """Fail-closed lint: span>=min, positive prices where present, max gap<=limit.

    Returns (ok, reason). Missing/empty frame or uncomputable check => FAIL.
    """
    if df is None or len(df) == 0 or "date" not in df.columns:
        return False, "empty"
    d = pd.to_datetime(df["date"])
    span = (d.max() - d.min()).days
    if span < min_span_days:
        return False, f"span {span}d < {min_span_days}d"
    for col in price_cols:
        if col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(s) == 0 or (s <= 0).any():
                return False, f"price {col} non-positive/empty"
    gaps = d.sort_values().diff().dt.days.dropna()
    if len(gaps) and gaps.max() > max_gap_days:
        return False, f"gap {int(gaps.max())}d > {max_gap_days}d"
    return True, "ok"


def manifest_row(family, symbol, start, end, rows, max_gap):
    """Manifest row compatible with campaign/team/lib/manifest.py."""
    return {"family": family, "symbol": symbol, "start": start,
            "end": end, "rows": rows, "max_gap_days": max_gap}


def write_csv(dirpath, name, df):
    """Write canonical csv into dirpath; returns path."""
    import os
    os.makedirs(dirpath, exist_ok=True)
    p = os.path.join(dirpath, name)
    df.to_csv(p, index=False)
    return p
