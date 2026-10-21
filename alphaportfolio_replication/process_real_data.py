"""
process_real_data.py
--------------------
Convert the real (free) daily OHLCV data from stockanalysis.com into a monthly
cross-sectional panel with characteristics, then into the lagged feature tensors
used by the AlphaPortfolio model (12-month lookback, K=11), matching the paper.

Characteristics built from real price/volume data (documented proxies since the
data lacks accounting fields / shares outstanding):
  ret1        1-month return            (short-term reversal signal)
  mom_3_1     3-month cum ret skip 1
  mom_6_1     6-month cum ret skip 1
  mom_12_1   12-month cum ret skip 1    (standard momentum)
  vol_mo      monthly volatility (std of daily returns)
  vol_6m      6-month volatility
  amihud      Amihud illiquidity |ret|/dollar-vol
  ln_dvol     log dollar volume (liquidity)
  ln_price    log price (size proxy, since no shares outstanding)
  turnover    monthly dollar volume
"""
import json, os
import numpy as np
import pandas as pd

CACHE = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/raw/prices_cache.json"
OUT_PANEL = "/Users/daxu/software/world-trader/alphaportfolio_replication/data/monthly_panel.csv"


def daily_to_monthly(df):
    df = df.sort_values("date").copy()
    df["date"] = pd.to_datetime(df["date"])
    df["ym"] = df["date"].dt.to_period("M")
    df["daily_ret"] = df["adj"].pct_change()
    df["dollar_vol"] = df["adj"] * df["volume"]
    g = df.groupby("ym")
    mo = g.agg(
        adj_last=("adj", "last"),
        ret1=("adj", lambda s: s.iloc[-1] / s.iloc[0] - 1 if len(s) else np.nan),
        vol_mo=("daily_ret", "std"),
        dvol=("dollar_vol", "sum"),
    ).reset_index()
    mo["symbol"] = df["symbol"].iloc[0]
    return mo


def add_momentum(panel):
    """Add longer-horizon momentum from the monthly adj_last series (skip-last)."""
    for m in (3, 6, 12):
        panel[f"mom_{m}_1"] = panel.groupby("symbol")["adj_last"].pct_change(m)
    return panel


def build_characteristics(monthly):
    d = monthly.sort_values(["symbol", "ym"]).copy()
    d["ln_price"] = np.log(d["adj_last"].clip(lower=1e-6))
    d["ln_dvol"] = np.log(d["dvol"].clip(lower=1e-6))
    d["amihud"] = (np.abs(d["ret1"]).clip(lower=1e-6)) / (d["dvol"].clip(lower=1e-6) + 1e-9)
    d["turnover"] = d["dvol"]
    # volatility scale to monthly % terms
    d["vol_mo"] = d["vol_mo"] * 100.0
    # 6-month volatility via expanding(std) over past 6 monthly vol
    d["vol_6m"] = d.groupby("symbol")["vol_mo"].transform(
        lambda s: s.rolling(6, min_periods=1).mean())
    d["ret1"] = d["ret1"] * 100.0
    for m in (3, 6, 12):
        d[f"mom_{m}_1"] = d[f"mom_{m}_1"] * 100.0
    # cross-sectional ranks
    for c in ["ret1", "mom_3_1", "mom_6_1", "mom_12_1", "vol_mo", "vol_6m",
              "amihud", "ln_dvol", "ln_price", "turnover"]:
        d[f"r_{c}"] = d.groupby("ym")[c].rank(pct=True)
    # interactions
    d["mom_12_x_size"] = d["r_mom_12_1"] * d["r_ln_price"]
    d["mom_12_x_vol"] = d["r_mom_12_1"] * d["r_vol_mo"]
    return d


FEATURES = [
    "ret1", "mom_3_1", "mom_6_1", "mom_12_1", "vol_mo", "vol_6m",
    "amihud", "ln_dvol", "ln_price", "turnover",
    "r_ret1", "r_mom_3_1", "r_mom_6_1", "r_mom_12_1", "r_vol_mo",
    "r_vol_6m", "r_amihud", "r_ln_dvol", "r_ln_price", "r_turnover",
    "mom_12_x_size", "mom_12_x_vol",
]


def main():
    cache = json.load(open(CACHE))
    daily_frames = [pd.DataFrame(v) for v in cache.values()]
    df_all = pd.concat(daily_frames, ignore_index=True)
    df_all["date"] = pd.to_datetime(df_all["date"])
    df_all["ym"] = df_all["date"].dt.to_period("M")
    print("daily rows:", len(df_all))

    monthly = pd.concat([daily_to_monthly(df) for df in daily_frames], ignore_index=True)
    monthly = add_momentum(monthly)
    monthly = build_characteristics(monthly)
    monthly["ym"] = monthly["ym"].astype(str)
    monthly.to_csv(OUT_PANEL, index=False)
    print("monthly panel:", monthly.shape)
    print("period:", monthly["ym"].min(), "->", monthly["ym"].max())
    print("stocks per month:", monthly.groupby("ym").size().mean().round(1))
    print("features:", len(FEATURES))


if __name__ == "__main__":
    main()
