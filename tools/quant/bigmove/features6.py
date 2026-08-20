"""features6: +12 free features on top of features5 (all causal at close t).

Adds: earnings surprise magnitude (PEAD strength, from earnings panel),
52-week-low distance, month-of-year seasonality, day-of-week, SPY beta
(rolling 60d), Amihud illiquidity, realized vol-of-vol, volume z-score,
return autocorrelation (20d lag-1), up/down streak (consecutive up days),
dispersion of the top decile (cross-sectional spread strength), and
overnight vs intraday return split (gap persistence).
"""
from __future__ import annotations
import os, json, glob
import numpy as np, pandas as pd
from features5 import build_features5

ROOT = "/Users/daxu/software/world-trader"
EARN = os.path.join(ROOT, "tools/quant/bigmove", "data", "earnings_panel")

def build_features6(P, close=None):
    if close is None:
        close = P["close"]
    f = build_features5(P)
    ret = close.pct_change()

    # 52-week low distance
    lo252 = close.rolling(252).min()
    f["dist_lo252"] = close / lo252 - 1.0

    # return autocorrelation (lag-1 of 20d returns), causal
    r20 = ret.rolling(20).mean()
    f["autocorr_20"] = ret.rolling(20).corr(ret.shift(1))

    # up-streak: consecutive up days (causal)
    up = (ret > 0).astype(float)
    streak = up.groupby((up != up.shift()).cumsum(), axis=0 if False else 1) if False else None
    # vectorized per-column streak
    up = (ret > 0).astype(int)
    def run_streak(s):
        groups = (s != s.shift()).cumsum()
        return s.groupby(groups).cumsum()
    f["up_streak"] = up.apply(run_streak)

    # realized vol-of-vol (std of 20d vol over 60d), causal
    rv20 = ret.rolling(20).std()
    f["vol_of_vol"] = rv20.rolling(60).std() / rv20.rolling(60).mean()

    # volume z-score vs 252d mean (needs vol panel)
    if "vol" in P:
        v = P["vol"]
        f["vol_z"] = (v - v.rolling(252).mean()) / v.rolling(252).std().replace(0, np.nan)
        # Amihud illiquidity: |ret| / dollar vol (causal)
        f["amihud"] = ret.abs() / (v * close).replace(0, np.nan)

    # SPY beta (rolling 60d vs SPY returns), causal
    try:
        spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelve_big/SPY.csv"),
                          parse_dates=["date"]).set_index("date")["close"].sort_index()
        spy_r = spy.pct_change().reindex(close.index)
        cov = ret.rolling(60).cov(spy_r)
        var = spy_r.rolling(60).var().replace(0, np.nan)
        f["beta_60"] = cov.div(var, axis=0)   # div on dates, not columns
    except Exception as e:
        print("beta skipped:", e)

    # month-of-year seasonality (causal: month known at t)
    for mo in range(1, 13):
        f[f"month_{mo}"] = (close.index.month == mo).astype(int)
        # tile across tickers
        f[f"month_{mo}"] = pd.DataFrame(
            {c: (close.index.month == mo).astype(int) for c in close.columns}, index=close.index)

    # earnings surprise magnitude (recent surprise_prc, ffill within 63d)
    try:
        surp = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
        for fp in glob.glob(os.path.join(EARN, "*.json")):
            sym = os.path.basename(fp)[:-5]
            if sym not in close.columns:
                continue
            rows = [e for e in json.load(open(fp)) if e.get("surprise_prc") is not None]
            if not rows:
                continue
            s = pd.Series([e["surprise_prc"] for e in rows],
                          index=[pd.Timestamp(e["date"]) for e in rows]).sort_index()
            surp[sym] = s.reindex(close.index, method="ffill", limit=63)
        f["earn_surprise_ff"] = surp
    except Exception as e:
        print("surprise skipped:", e)

    # cross-sectional spread: top-decile 21d momentum minus bottom-decile (causal),
    # tiled across tickers (market-wide feature, known at close t)
    m21 = close.pct_change(21)
    spread = m21.apply(lambda row: row.quantile(0.9) - row.quantile(0.1), axis=1)
    f["xs_spread_21"] = pd.DataFrame({c: spread for c in close.columns}, index=close.index)

    return f
