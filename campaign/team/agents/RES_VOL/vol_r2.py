"""RES_VOL R2 lib — spliced SPX price levels (FRED spy_early 1993-2005 + SPY 2006-09+).

Root-cause fix (TDD test_spliced_spx_returns_prices_not_returns): the R2 draft passed
RETURNS into long_book(px=...), whose pct_change() produced rpu as low as -162 (day after a
near-zero return; -51.8 net on 2015-08-31). Books take PRICE LEVELS; this module is the
single place that builds them. D.closes() is currently broken by twelve_big/manifest.csv
(no 'date' column) — loader avoided, files read directly (flagged to DATA_ORGANIZE).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from campaign.harness import data as D

SPY_TWELVE = "/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv"


def spliced_spx():
    """Base-100 compounded spliced SPX price levels; seam-day return nulled (2006 gap)."""
    e = D.fred("spy_early")
    b = pd.read_csv(SPY_TWELVE, parse_dates=["date"], index_col="date")["close"].astype(float)
    re_, rb = e.pct_change(), b.pct_change()
    r = pd.concat([re_[re_.index < "2006-01-01"], rb[rb.index >= "2006-09-01"]])
    r = r[~r.index.duplicated(keep="last")].sort_index()
    r.loc[b.index[b.index >= "2006-09-01"][0]] = np.nan
    return (1.0 + r.dropna()).cumprod() * 100.0
