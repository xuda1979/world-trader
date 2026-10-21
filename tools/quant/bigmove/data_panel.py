"""Load the US large-cap daily panel and compute next-day returns + base rates.

Return defined as:  next_close / today_close - 1   (signal at close of date T
uses info available at T, target = close(T) -> close(T+1)).
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelve_big")

# Non-US ADRs + index/benchmark ETFs present in twelve_big -> exclude (keep real US equities)
BLOCKLIST = {"QQQ", "SPY", "XLF", "ASML", "HMC", "TM"}

MIN_HISTORY = 252  # need at least a year of history to build features


def load_prices(min_history: int = MIN_HISTORY):
    """Load all US common stocks -> DataFrame[date, ticker] of close prices."""
    data = {}
    for fn in os.listdir(DATA_DIR):
        if not fn.upper().endswith(".CSV"):
            continue
        sym = fn[:-4]
        if sym in BLOCKLIST:
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, fn), parse_dates=["date"])
        if df.empty or "close" not in df.columns:
            continue
        df = df.sort_values("date").set_index("date")
        df = df[~df.index.duplicated(keep="last")]["close"]
        df = df.dropna()
        if len(df) < min_history:
            continue
        data[sym] = df
    panel = pd.DataFrame(data).sort_index()
    return panel


def build_target(close: pd.DataFrame):
    """Target: next-day return close(T)->close(T+1). Returned aligned so that
    row T holds return realized over T->T+1, computed only from close data."""
    ret_next = close.pct_change().shift(-1)   # ret_next[T] = close[T+1]/close[T]-1
    return ret_next


if __name__ == "__main__":
    close = load_prices()
    print(f"Panel: {close.shape[1]} tickers x {close.shape[0]} days "
          f"({close.index.min().date()}..{close.index.max().date()})")
    ret_next = build_target(close)

    # ---- base rates of next-day |move| and big moves ----
    big_up = (ret_next >= 0.05)
    big_down = (ret_next <= -0.05)
    big_abs = (ret_next.abs() >= 0.05)

    n_obs = int(ret_next.notna().sum().sum())
    n_day_stock = close.notna().sum().sum()
    print(f"\nTotal stock-day observations (with close): {n_day_stock:,}")
    print(f"Total next-day return observations        : {n_obs:,}")

    for label, mask in [("up>=5%", big_up), ("down<=-5%", big_down), ("|move|>=5%", big_abs)]:
        cnt = int((mask & ret_next.notna()).sum().sum())
        print(f"  next-day {label:>10}: {cnt:8,}  ({cnt/n_obs:.4%} of obs)")

    # per-stock coverage of big moves
    cnt_per = (big_abs & ret_next.notna()).sum(axis=0)
    cnt_per = cnt_per[cnt_per > 0].sort_values(ascending=False)
    print(f"\nStocks with ANY |next-day move|>=5%: {len(cnt_per)} of {close.shape[1]}")
    print("Top 15 stocks by count of |next-day move|>=5%:")
    print(cnt_per.head(15).to_string())
    print("\nDistribution of per-stock big-move counts:")
    print(cnt_per.describe().to_string())
