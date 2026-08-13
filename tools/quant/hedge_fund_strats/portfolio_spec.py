"""Deployment spec for the recommended all-weather portfolio (12 bps RT).

Construction (per RESEARCH_REPORT.md "Bottom line", resolved 2026-08-13):

  Sleeve 1 — hedge 3-stream EW (monthly): L/S 130/30 + CTA futures macro
            21d + Global Macro, equal weight, ex stat arb. Cost-inclusive
            at 6 bps/side via the suite engine (results/equity_*.csv).
  Sleeve 2 — AP gold composite (daily): alphaportfolio_replication/data/
            wf_champion_gold_opt_daily.csv — realization-timed daily
            record of the gold-static champion, net of 6 bps one-way.
  Sleeve 3 — Polygon LS champion (daily): tools/quant/ls/results/
            levdet3.0/daily_returns.csv, re-costed 3.8 -> 6 bps/side via
            its turnover series (blend_6stream.load_ls_champion).

  Weights: sleeve EW. 2008+ : h3 50% + AP 50%.
          2024+ (LS live): h3 33.3% + AP 33.3% + LS 33.3%.

Expected stats (12 bps RT):
  2008-2026 monthly:  SR 0.94, +10.7%/yr, MaxDD -10.1%, positive in all
  4 sub-periods, every 5y rolling window SR > 0 (min +0.25).
  2024+ daily:        SR 1.15, +11.4%/yr, MaxDD -5.6% (h3+AP+LS).

Outputs: results/portfolio_weights.csv (daily sleeve weights + portfolio
return) and results/recommended_portfolio.json (this spec as data).

Usage:  python tools/quant/hedge_fund_strats/portfolio_spec.py
"""

import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from blend_6stream import load_ap_gold, load_ls_champion, load_hedge_streams  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

SPEC = {
    "name": "all-weather portfolio (h3 + AP gold + LS champion)",
    "cost_bps_one_side": 6.0,
    "rebalance": "sleeves rebalanced monthly (AP and hedge are monthly-cadence by construction); LS champion trades on its own 21d schedule",
    "sleeves": {
        "hedge_3stream_ew": {
            "legs": ["L/S 130/30", "CTA futures macro 21d", "Global Macro"],
            "weights_inside": [1/3, 1/3, 1/3],
            "source": "hedge_fund_strats/results/equity_*.csv (12 bps RT)",
        },
        "ap_gold": {
            "source": "alphaportfolio_replication/data/wf_champion_gold_opt_daily.csv",
            "cost": "6 bps one-way embedded, realization-timed",
        },
        "ls_champion": {
            "source": "tools/quant/ls/results/levdet3.0/daily_returns.csv",
            "cost": "re-costed 3.8 -> 6 bps/side via turnover",
        },
    },
    "weights": {
        "2008_to_2024": {"hedge_3stream_ew": 0.5, "ap_gold": 0.5, "ls_champion": 0.0},
        "2024_plus": {"hedge_3stream_ew": 1/3, "ap_gold": 1/3, "ls_champion": 1/3},
    },
}


def main():
    h = load_hedge_streams()
    h3 = pd.concat([h["ls"], h["cta"], h["macro"]], axis=1).mean(axis=1)
    ap = load_ap_gold()
    ls = load_ls_champion()

    w_h = SPEC["weights"]["2008_to_2024"]
    w_l = SPEC["weights"]["2024_plus"]

    hedge_w = pd.Series(w_h["hedge_3stream_ew"], index=h3.index)
    ap_w = pd.Series(w_h["ap_gold"], index=ap.index)
    # trading-day grid only — a calendar grid (freq='D') would create
    # weekend rows that ffill returns onto and inflate daily SR
    grid = h3.index.union(ap.index).union(ls.index)
    ls_w = pd.Series(0.0, index=grid)

    # 2024+ window: switch to 3-sleeve weights
    cut = pd.Timestamp("2024-07-01")
    hedge_w.loc[hedge_w.index >= cut] = w_l["hedge_3stream_ew"]
    ap_w.loc[ap_w.index >= cut] = w_l["ap_gold"]
    ls_w.loc[ls_w.index >= cut] = w_l["ls_champion"]

    f = pd.concat({"h3": h3, "ap": ap, "ls": ls}, axis=1)
    # natural concat alignment (union of trading days); LS weight is 0
    # before its window and its missing returns contribute nothing
    w = pd.DataFrame({"h3": hedge_w, "ap": ap_w, "ls": ls_w}).reindex(f.index).ffill()
    w["ls"] = w["ls"].fillna(0.0)
    rets = f.copy()
    rets["ls"] = rets["ls"].fillna(0.0)
    port = (w["h3"] * rets["h3"] + w["ap"] * rets["ap"] + w["ls"] * rets["ls"]).dropna()

    out = pd.DataFrame({"portfolio_return": port, **w.loc[port.index].to_dict("series")})
    out.index.name = "date"
    out.to_csv(os.path.join(RESULTS, "portfolio_weights.csv"))

    # stats card — full window (h3+AP since 2008) and live window (2024+)
    def card(r):
        r = r.dropna()
        g = (1 + r).cumprod()
        mdd = (g / g.cummax() - 1).min()
        ann = (1 + r).prod() ** (252 / len(r)) - 1
        sr = (r.mean() * 252 - 0.02) / (r.std() * np.sqrt(252))
        return {
            "window": [str(r.index.min().date()), str(r.index.max().date())],
            "n_days": int(len(r)),
            "sharpe": round(float(sr), 3),
            "ann_return_pct": round(float(ann) * 100, 2),
            "max_drawdown_pct": round(float(mdd) * 100, 2),
        }

    cut = pd.Timestamp("2024-07-01")
    spec = dict(SPEC)
    spec["actual_stats"] = {
        "full_2008_plus": card(port[port.index < cut]),
        "live_2024_plus": card(port[port.index >= cut]),
    }
    with open(os.path.join(RESULTS, "recommended_portfolio.json"), "w") as fh:
        json.dump(spec, fh, indent=2, default=str)
    print(json.dumps(spec["actual_stats"], indent=2))
    print("saved -> results/portfolio_weights.csv + results/recommended_portfolio.json")


if __name__ == "__main__":
    import numpy as np  # noqa: F401  (used in main)

    main()
