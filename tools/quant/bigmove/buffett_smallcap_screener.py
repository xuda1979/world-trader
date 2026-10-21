"""Buffett small-cap / Graham net-net (烟蒂股) screener built on the existing
free-data EDGAR fundamentals panel.

Maps Buffett's stated $1M / 50%-per-year strategy to what this repo can
actually compute from its point-in-time SEC fundamentals + local prices:

  NCAV (Net Current Asset Value) = current_assets - total_liabilities
                                  = cur_assets - (assets - book_equity)
  net-net trigger              = market_cap < NCAV   (price below net current assets)
  micro-cap band               = market_cap in ~$50M-$2B (Buffett invested in the
                                                          bottom band Wall St ignores)
  cash special                 = cash per share > price  (like Union Street Railway)

Point-in-time: uses 'filed' dates in the panel so no lookahead. Forward returns
come from the local price panel (shifted), so the historical edge is testable.
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = "/Users/daxu/software/world-trader"
os.chdir(HERE)

def load_prices():
    from pipeline_common import load_ohlcv
    P = load_ohlcv(min_history=200)
    return P["close"]

def main():
    df = pd.read_parquet("data/edgar_chars.parquet")
    close = load_prices()
    mclose = close.resample("ME").last()

    df = df.dropna(subset=["cur_assets", "assets", "book_equity", "cur_liab", "shares", "mcap"]).copy()
    df["price"] = df["mcap"]                      # mcap col is really month-end price
    df["mktcap"] = df["shares"] * df["price"]     # true market cap (USD)
    df["total_liab"] = df["assets"] - df["book_equity"]
    df["ncav"] = df["cur_assets"] - df["total_liab"]
    df["ncav_mc_ratio"] = df["ncav"] / df["mktcap"].replace(0, np.nan)  # >1 = net-net
    df["cash_ps"] = df["cash"] / df["shares"]
    df["cash_over_price"] = df["cash_ps"] / df["price"].replace(0, np.nan)
    df["pe_est"] = df["price"] / (df["net_income"] / df["shares"]).replace(0, np.nan)

    # forward returns from price panel
    mret = mclose.pct_change().stack(); mret.index.names = ["month", "ticker"]
    mi = pd.MultiIndex.from_frame(df[["month", "ticker"]])
    df["ret_1m"] = mret.shift(-1).reindex(mi).to_numpy()
    for h in (3, 6, 12):
        r = (mclose / mclose.shift(h) - 1.0).stack(); r.index.names = ["month", "ticker"]
        df[f"ret_{h}m"] = r.shift(-h).reindex(mi).to_numpy()

    # clean: price >= $2, drop extremes
    df = df[df["price"] >= 2.0]
    df = df[(df["ret_1m"] >= -0.95) & (df["ret_1m"] <= 2.5)]

    # Buffett micro-cap band: Wall St ignores sub-$2B; $50M floor for tradability
    df["microcap"] = (df["mktcap"] >= 5e7) & (df["mktcap"] <= 2e9)
    df["netnet"] = (df["ncav_mc_ratio"] > 1.0) & df["microcap"]
    df["cash_special"] = (df["cash_over_price"] > 1.0) & df["microcap"]
    df["deep_value"] = (df["pe_est"] > 0) & (df["pe_est"] < 5) & df["microcap"]

    # ---- LIVE candidates: most recent month with breadth ----
    live_month = df["month"].max()
    live = df[df["month"] == live_month]
    live = live.sort_values("ncav_mc_ratio", ascending=False)
    cols = ["ticker", "price", "mktcap", "book_equity", "ncav", "ncav_mc_ratio",
            "cash_ps", "cash_over_price", "pe_est", "netnet", "cash_special", "deep_value"]
    print(f"\n=== LIVE NET-NET SCREEN ({pd.Timestamp(live_month).date()}) ===")
    print(f"names in universe: {len(live)}, micro-caps: {int(live.microcap.sum())}")
    top = live[live.microcap].head(15)[cols]
    with pd.option_context("display.float_format", lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}", "display.max_columns", None, "display.width", 220):
        print(top.to_string(index=False))
    ns = live[live.netnet]
    print(f"\ncurrent net-nets (mcap < NCAV, microcap): {len(ns)}")
    if len(ns):
        with pd.option_context("display.float_format", lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}", "display.max_columns", None, "display.width", 220):
            print(ns[cols].drop(columns=["netnet","cash_special","deep_value"]).head(20).to_string(index=False))
    cs = live[live.cash_special & ~live.netnet]
    print(f"\ncurrent cash specials (cash/price>1, microcap, not net-net): {len(cs)}")
    if len(cs):
        with pd.option_context("display.float_format", lambda x: f"{x:,.0f}" if abs(x) >= 1e3 else f"{x:.2f}", "display.max_columns", None, "display.width", 220):
            print(cs[cols].drop(columns=["netnet","cash_special","deep_value"]).head(10).to_string(index=False))

    # ---- HISTORICAL VALIDATION of the edge ----
    def avg_ret(flag, name):
        s = df[flag & df["microcap"]]
        base = df[df["microcap"]]
        out = {"n_months": s.month.nunique(), "n_obs": len(s)}
        for h in ("1m", "3m", "6m", "12m"):
            out[f"ret_{h}"] = float(s[f"ret_{h}"].mean())
            out[f"base_{h}"] = float(base[f"ret_{h}"].mean())
        return out

    print("\n=== HISTORICAL EDGE (micro-cap universe, point-in-time) ===")
    res = {
        "microcap_all": avg_ret(df["microcap"].astype(bool), "all micro"),
        "netnet": avg_ret(df["netnet"], "net-net"),
        "cash_special": avg_ret(df["cash_special"], "cash special"),
        "deep_value": avg_ret(df["deep_value"], "PE<5 value"),
    }
    for k, v in res.items():
        print(f"{k:14s} n_obs={v['n_obs']:6d} | 1m {v['ret_1m']*100:6.2f}% (base {v['base_1m']*100:.2f}%) "
              f"| 3m {v['ret_3m']*100:6.2f}% (base {v['base_3m']*100:.2f}%) "
              f"| 6m {v['ret_6m']*100:6.2f}% (base {v['base_6m']*100:.2f}%) "
              f"| 12m {v['ret_12m']*100:6.2f}% (base {v['base_12m']*100:.2f}%)")
    outpath = os.path.join(ROOT, "tools/quant/reports/buffett_smallcap_screen.json")
    with open(outpath, "w") as f:
        json.dump({"as_of": str(pd.Timestamp(live_month).date()),
                   "live_candidates": live[live.microcap][["ticker","price","mktcap","ncav","ncav_mc_ratio","cash_over_price","pe_est","netnet","cash_special","deep_value"]].head(30).to_dict("records"),
                   "historical_edge": res}, f, indent=2, default=float)
    print(f"\nwrote {outpath}")

if __name__ == "__main__":
    main()
