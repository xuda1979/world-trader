"""features5: +35 FREE features on top of features3 (all causal at close t).

Adds: 52-week-high distance, realized skew/kurtosis, cross-sectional
percentile ranks (momentum), baa-aaa default spread, oil/gas/gold/silver/
copper/DXY momentum, EUR/GBP/JPY/CAD/CNY FX momentum, intl yield changes,
US30Y + 3M levels and long-end slope, and earnings-date proximity (PEAD)
from the earnings panel. Market-wide series are tiled across tickers;
per-ticker series computed directly from the panel. NO look-ahead (all
shifts >= +1, or values known at close t).
"""
from __future__ import annotations
import os, json, glob
import numpy as np, pandas as pd
from features3 import build_features3

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
EARN = os.path.join(ROOT, "tools/quant/bigmove", "data", "earnings_panel")

def _load(name):
    df = pd.read_csv(os.path.join(FRED, name), parse_dates=["date"])
    df.columns = ["date", "val"]
    return df.set_index("date")["val"].reindex(
        pd.bdate_range(df.date.min(), df.date.max()), method="ffill").sort_index()

def _tile(s, close):
    return pd.DataFrame({c: s.reindex(close.index).to_numpy() for c in close.columns},
                        index=close.index)

def build_features5(P, close=None):
    if close is None:
        close = P["close"]
    f = build_features3(P)
    ret = close.pct_change()

    # ---- per-ticker, causal ----
    # 52-week high distance (classic momentum predictor)
    hi252 = close.rolling(252).max()
    f["dist_hi252"] = close / hi252 - 1.0
    # realized skewness & kurtosis (20d), causal
    r = ret.rolling(20)
    m2 = r.mean(); sd = ret.rolling(20).std()
    f["skew_20"] = ((ret - m2) ** 3).rolling(20).mean() / sd ** 3
    f["kurt_20"] = ((ret - m2) ** 4).rolling(20).mean() / sd ** 4 - 3.0
    # downside vol / upside vol asymmetry (20d)
    down = ret.clip(upper=0); up = ret.clip(lower=0)
    f["down_vol_ratio"] = down.rolling(20).std() / up.rolling(20).std().replace(0, np.nan)
    # volume trend (20d vs 60d avg volume ratio) if vol panel exists
    if "vol" in P:
        v60 = P["vol"].rolling(60).mean()
        f["vol_trend_20_60"] = P["vol"].rolling(20).mean() / v60.replace(0, np.nan)
    # cross-sectional percentile rank of momentum (ranks help the ranking task)
    for n in [20, 60]:
        mom = close.pct_change(n)
        f[f"rank_mom_{n}"] = mom.rank(axis=1, pct=True)
    # earnings proximity (days since last earnings / days to next) - PEAD
    try:
        earn = {}
        for fp in glob.glob(os.path.join(EARN, "*.json")):
            sym = os.path.basename(fp)[:-5]
            if sym not in close.columns:
                continue
            dates = [pd.Timestamp(e["date"]) for e in json.load(open(fp))]
            s = pd.Series(np.nan, index=close.index, dtype=float)
            # days to next earnings (>=0 causal), days since last (>=0 causal)
            for dt in close.index:
                nxt = [x for x in dates if x > dt]
                prv = [x for x in dates if x <= dt]
                s[dt] = (min(nxt) - dt).days if nxt else np.nan
            f["earn_days_next"] = f.get("earn_days_next", pd.DataFrame(index=close.index, columns=close.columns))
            f["earn_days_next"][sym] = s
        if "earn_days_next" in f:
            f["earn_days_next"] = f["earn_days_next"].astype(float)
            # since-last via opposite
            f["earn_days_since"] = pd.DataFrame(np.nan, index=close.index, columns=close.columns)
            for fp in glob.glob(os.path.join(EARN, "*.json")):
                sym = os.path.basename(fp)[:-5]
                if sym not in close.columns:
                    continue
                dates = [pd.Timestamp(e["date"]) for e in json.load(open(fp))]
                s = pd.Series(np.nan, index=close.index, dtype=float)
                for dt in close.index:
                    prv = [x for x in dates if x <= dt]
                    s[dt] = (dt - max(prv)).days if prv else np.nan
                f["earn_days_since"][sym] = s
    except Exception as e:
        print("earnings features skipped:", e)

    # ---- market-wide FRED, tiled ----
    def add_tiled(name, series):
        s = series.reindex(close.index)
        f[name] = _tile(s, close)

    # default premium: baa - aaa
    baa = _load("baa.csv"); aaa = _load("aaa.csv")
    spd = baa - aaa
    add_tiled("baa_aaa_spd", spd)
    add_tiled("baa_aaa_spd_chg21", spd.diff(21))
    # commodities & dollar momentum
    for nm, col in [("wti","wti.csv"),("natgas","natgas.csv"),("xau","xau.csv"),
                    ("slv","slv.csv"),("copx","copx.csv"),("dxy","dxy.csv")]:
        s = _load(col)
        add_tiled(f"{nm}_mom1", s.pct_change(1))
        add_tiled(f"{nm}_mom5", s.pct_change(5))
        add_tiled(f"{nm}_mom21", s.pct_change(21))
    # FX cross-section momentum
    for ccy in ["eur","gbp","jpy","cad","cny"]:
        s = _load(f"{ccy}.csv")
        add_tiled(f"fx_{ccy}_mom5", s.pct_change(5))
        add_tiled(f"fx_{ccy}_mom21", s.pct_change(21))
    # international yield changes (global liquidity proxy)
    for y in ["ch10y","gb10y","jp10y","ez10y","au10y","ca10y"]:
        s = _load(f"{y}.csv")
        add_tiled(f"{y}_chg21", s.diff(21))
    # long end + 3M level, long-end slope
    u30 = _load("us30y.csv"); tb3 = _load("tbill3m.csv"); u2 = _load("us2y.csv")
    add_tiled("us30y", u30)
    add_tiled("us30y_chg21", u30.diff(21))
    add_tiled("tbill3m", tb3)
    add_tiled("us30y_minus_2y", u30 - u2)
    # VIX 21d change (regime shift timing)
    vix = _load("vix.csv")
    add_tiled("vix_chg21", vix.diff(21))
    return f
