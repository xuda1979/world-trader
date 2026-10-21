"""Add FRED macro / risk-appetite signals (VIX, yield curve, DXY, rates, oil,
credit, commodities) to the feature set. These macro-regime features help flag
high-volatility days when individual stocks are more likely to have big moves.
All values are known at close(T) -> no look-ahead. Broadcast acroos tickers.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from features3 import build_features3

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")


def _tile(s: pd.Series, cols) -> pd.DataFrame:
    return pd.DataFrame({c: s for c in cols}, index=s.index)


def _load(name):
    df = pd.read_csv(os.path.join(FRED, name), parse_dates=["date"])
    df.columns = ["date", "val"]
    return df.set_index("date")["val"].sort_index()


def build_features4(P, close=None):
    if close is None:
        close = P["close"]
    f = build_features3(P, close)

    def add(name, series):
        s = series.reindex(close.index)
        f[name] = _tile(s, close.columns)

    # VIX (implied vol) - level + rate of change + regime
    vix = _load("vix.csv")
    add("vix", vix)
    add("vix_chg5", vix.diff(5))
    add("vix_chg20", vix.diff(20))
    add("vix_ratio_ma63", vix / vix.rolling(63).mean())
    add("vix_z", (vix - vix.rolling(252).mean()) / vix.rolling(252).std())

    # yield curve 10y-2y (macro/inversion regime)
    t10y2y = _load("t10y2y.csv")
    add("t10y2y", t10y2y)
    add("t10y2y_chg20", t10y2y.diff(20))
    add("t10y2y_ma20", t10y2y.rolling(20).mean())

    # rates - 10y and 2y levels & changes
    us10y = _load("us10y.csv")
    us2y = _load("us2y.csv")
    add("us10y", us10y)
    add("us10y_chg5", us10y.diff(5))
    add("us10y_chg20", us10y.diff(20))
    add("us2y", us2y)
    add("us10y_2y_spread", us10y - us2y)

    # DXY dollar index (risk-on/off, multinational earnings translation)
    dxy = _load("dxy.csv")
    add("dxy", dxy)
    add("dxy_ret1", dxy.pct_change())
    add("dxy_ret20", dxy / dxy.shift(20) - 1.0)

    # oil (brent)
    brent = _load("brent.csv")
    add("brent_ret1", brent.pct_change())
    add("brent_ret20", brent / brent.shift(20) - 1.0)
    add("brent_vol20", brent.pct_change().rolling(20).std())

    # high-yield OAS credit stress (only 2023+, NaN earlier; XGBoost handles)
    try:
        hy = _load("hy_oas.csv")
        add("hy_oas", hy)
        add("hy_oas_chg5", hy.diff(5))
    except Exception:
        pass

    # commodities / metals as risk proxies
    try:
        copper = _load("copper_monthly.csv")
        add("copper_ret", copper.pct_change().ffill())
    except Exception:
        pass
    try:
        slv = _load("slv.csv")
        add("slv_ret5", slv.pct_change().rolling(5).sum())
    except Exception:
        pass

    return f


if __name__ == "__main__":
    from pipeline_common import load_ohlcv
    P = load_ohlcv()
    f = build_features4(P)
    print(f"features4 total: {len(f)} feature families")
    macro = [k for k in f if k.startswith(('vix','t10','us10','us2','dxy','brent','hy','copper','slv'))]
    print("macro keys:", macro)
