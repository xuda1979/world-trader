"""Enhanced features: per-stock technicals + MARKET-REGIME and CROSS-SECTIONAL
signals (Fama-French factors, market momentum/vol, cross-sectional breadth,
crypto/FX risk-on proxies). All exogenous features are known at close(T) and
broadcast acoross tickers -> no look-ahead.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd
from features2 import build_features2

ROOT = "/Users/daxu/software/world-trader"
DATA = os.path.join(ROOT, "tools/quant/data")


def _tile(s: pd.Series, cols) -> pd.DataFrame:
    return pd.DataFrame({c: s for c in cols}, index=s.index)


def load_ff_factors():
    """Fama-French daily factors (Mkt-RF, SMB, HML, RF) + momentum MOM."""
    factors = {}
    ff_path = os.path.join(DATA, "ff_factors", "F-F_Research_Data_Factors_daily.csv")
    import csv
    rows = []
    with open(ff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith((".", "Mkt", "Copyright", "This", "Tbill")):
                continue
            parts = line.split(",")
            if len(parts) == 5 and parts[0].isdigit():
                rows.append((parts[0], float(parts[1]), float(parts[2]),
                             float(parts[3]), float(parts[4])))
    df = pd.DataFrame(rows, columns=["date", "MktRF", "SMB", "HML", "RF"])
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.set_index("date") / 100.0   # percent -> decimal

    mom_path = os.path.join(DATA, "ff_factors", "F-F_Momentum_Factor_daily.csv")
    mrows = []
    with open(mom_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith((".", "MOM", "Copyright", "This")):
                continue
            parts = line.split(",")
            if len(parts) == 2 and parts[0].isdigit():
                mrows.append((parts[0], float(parts[1])))
    mdf = pd.DataFrame(mrows, columns=["date", "MOM"])
    mdf["date"] = pd.to_datetime(mdf["date"], format="%Y%m%d")
    mdf = mdf.set_index("date") / 100.0
    out = df.join(mdf, how="left")
    return out


def load_market_series():
    """Market proxy (SPY) close + cross-sectional breadth from whole universe."""
    spy = pd.read_csv(os.path.join(DATA, "twelve_big", "SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"]
    return spy.sort_index()


def build_features3(P, close=None):
    """P: OHLCV dict (dates x tickers) from pipeline_common.load_ohlcv.
    Returns dict of feature DataFrames (dates x tickers), all causal at close(T)."""
    if close is None:
        close = P["close"]
    f = build_features2(P)   # the 49 per-stock technicals

    # ---- market/spy features ----
    spy = load_market_series().reindex(close.index).ffill()
    spy_ret = spy.pct_change()
    for n in [1, 5, 21, 63]:
        f[f"mkt_ret_{n}"] = _tile(spy / spy.shift(n) - 1.0, close.columns)
    for n in [10, 21, 63]:
        f[f"mkt_vol_{n}"] = _tile(spy_ret.rolling(n).std(), close.columns)
    f["mkt_rvol_ratio"] = _tile(spy_ret.rolling(63).std() / spy_ret.rolling(10).std(),
                                close.columns)
    f["mkt_dist_ma200"] = _tile(spy / spy.rolling(200).mean() - 1.0, close.columns)

    # ---- cross-sectional breadth: fraction of universe with big moves recently ----
    daily = close.pct_change()
    big5 = (daily.abs().rolling(5).sum() >= 0.15).mean(axis=1)  # share with high 5d chop
    f["xs_breadth_chop"] = _tile(big5, close.columns)
    xs_vol = daily.std(axis=1)
    f["xs_avg_vol"] = _tile(xs_vol, close.columns)
    f["xs_vol_ratio"] = _tile(xs_vol / xs_vol.rolling(63).mean(), close.columns)

    # ---- Fama-French factors (broadcast) ----
    ff = load_ff_factors().reindex(close.index).ffill()
    for col in ["MktRF", "SMB", "HML", "MOM"]:
        if col in ff.columns:
            s = ff[col]
            f[f"ff_{col}"] = _tile(s, close.columns)
    # market risk premium rolling
    f["ff_MktRF_ma5"] = _tile(ff["MktRF"].rolling(5).mean(), close.columns)
    f["ff_MktRF_ma21"] = _tile(ff["MktRF"].rolling(21).mean(), close.columns)

    # ---- crypto / FX risk-on proxies (NaN before start; XGBoost handles) ----
    try:
        btc = pd.read_csv(os.path.join(DATA, "binance", "BTC.csv"),
                          parse_dates=["date"]).set_index("date")["close"]
        btc = btc.reindex(close.index)
        f["btc_ret_1"] = _tile(btc.pct_change(), close.columns)
        f["btc_ret_5"] = _tile(btc / btc.shift(5) - 1.0, close.columns)
    except Exception:
        pass
    try:
        eur = pd.read_csv(os.path.join(DATA, "fx", "EUR_USD.csv"),
                          parse_dates=["date"]).set_index("date")["close"]
        eur = eur.reindex(close.index)
        f["eurusd_ret_5"] = _tile(eur / eur.shift(5) - 1.0, close.columns)
    except Exception:
        pass

    return f


if __name__ == "__main__":
    from pipeline_common import load_ohlcv
    P = load_ohlcv()
    f = build_features3(P)
    print(f"features3: {len(f)} feature families")
    print("sample of added keys:", [k for k in f if k.startswith(('mkt','xs','ff','btc','eur'))])
