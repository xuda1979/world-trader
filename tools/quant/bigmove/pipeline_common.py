"""Common data-loading helpers for the big-move strategy."""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
DATA_DIR = os.path.join(ROOT, "tools/quant/data/twelve_big")
BLOCKLIST = {"QQQ", "SPY", "XLF", "ASML", "HMC", "TM"}
MIN_HISTORY = 400   # need history to build 200MA etc.


def load_ohlcv(min_history: int = MIN_HISTORY):
    """Load full OHLCV panel for the universe -> dict of dates x ticker DataFrames."""
    fields = {"date": [], "open": [], "high": [], "low": [], "close": [], "vol": []}
    col_frames = {"open": {}, "high": {}, "low": {}, "close": {}, "vol": {}}
    for fn in sorted(os.listdir(DATA_DIR)):
        if not fn.upper().endswith(".CSV"):
            continue
        sym = fn[:-4]
        if sym in BLOCKLIST:
            continue
        df = pd.read_csv(os.path.join(DATA_DIR, fn), parse_dates=["date"])
        if df.empty or "close" not in df.columns:
            continue
        df = df.sort_values("date")
        df = df.drop_duplicates("date")
        df = df.set_index("date")
        # require sufficient history
        if len(df) < min_history:
            continue
        if df["close"].isna().any() or (df["close"] <= 0).any():
            continue
        for f in ["open", "high", "low", "close", "vol"]:
            col_frames[f][sym] = df[f]
    P = {}
    for f in ["open", "high", "low", "close", "vol"]:
        P[f] = pd.DataFrame(col_frames[f]).sort_index()
    return P
