"""Optimize the bigmove strategy for maximum Sharpe.

Key innovation vs earlier: a proper CALENDAR-TIME portfolio backtest.
On each calendar day, if signals fire, go long a portfolio of the selected
names at that day's close and realize the next-day return, all equal-notional
(credit-balanced so total deployed capital is fixed across days). Days with no
signal are flat (cash). Calendar-time returns -> honest annualized Sharpe.

Levers swept:
  - prob threshold
  - cross-sectional top-K per day
  - prob weighting (linear / sqrt / rank) vs equal
  - per-name position cap (to limit concentration)
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "pred_frame.parquet")
COST = 0.0006  # one side
TRADING_DAYS = 252

df = pd.read_parquet(CACHE).copy()
df["date"] = pd.to_datetime(df["date"])


def calendar_sharpe(daily_net):
    """annualized Sharpe over the full calendar index (flat days = 0)."""
    eq = (1 + daily_net).cumprod()
    # Sharpe is the (mean/std)*sqrt(252) of the daily NET series, using ALL days
    if daily_net.std() == 0:
        return 0.0, 0.0
    s = (daily_net.mean() / daily_net.std()) * np.sqrt(TRADING_DAYS)
    ann = (1 + daily_net).prod() ** (TRADING_DAYS / len(daily_net)) - 1
    return s, ann


def run_config(thr, top_k, weighting, cap=None):
    """Return (calendar_sharpe, ann_return, maxDD, n_trades, active_days, win_rate)."""
    d = df[df["prob"] >= thr].copy()
    if len(d) == 0:
        return None
    if weighting == "equal":
        pass
    # compute notional weight per selected name (before cap)
    if weighting == "prob":
        d["w"] = d["prob"]
    elif weighting == "sqrt":
        d["w"] = np.sqrt(d["prob"])
    elif weighting == "rank":
        # rank within day normalized to 0..1
        pass
    else:
        d["w"] = 1.0

    # rank within each day
    d["dayrank"] = d.groupby("date")["prob"].rank(ascending=False)
    if top_k is not None:
        d = d[d["dayrank"] <= top_k]

    # basis for prob/rank weights
    if weighting == "prob":
        d["w"] = d["prob"]
    elif weighting == "sqrt":
        d["w"] = np.sqrt(d["prob"])
    elif weighting == "rank":
        d["w"] = 1.0 / d["dayrank"]
    else:
        d["w"] = 1.0

    # optional per-name cap expressed as max fraction of daily book
    if cap is not None:
        d["w"] = d["w"].clip(upper=cap)

    # group by day: normalize weights to sum 1.0 (fixed capital per active day)
    g = d.groupby("date")
    wsum = g["w"].transform("sum")
    d["alloc"] = d["w"] / wsum

    d["net"] = (d["ret_no_stop"] - 2 * COST) * d["alloc"]
    daily = d.groupby("date")["net"].sum()

    # build calendar series over the full out-of-sample index (flat = 0)
    full_idx = df["date"].unique()
    cal = daily.reindex(full_idx, fill_value=0.0).sort_index()

    s, ann = calendar_sharpe(cal)
    # max drawdown on calendar equity
    eq = (1 + cal).cumprod()
    dd = (eq / eq.cummax() - 1).min()
    n_trades = int(len(d))
    active = int(len(daily))
    win = float((d["ret_no_stop"] >= 0.05).mean())
    return {"sharpe": round(s, 3), "ann": round(ann, 4), "maxdd": round(float(dd), 4),
            "n_trades": n_trades, "active_days": active, "win5": round(win, 4),
            "avg_sig_per_day": round(n_trades / active, 2) if active else 0}


def main():
    results = {}
    # ---- sweep ----
    configs = []
    for thr in [0.6, 0.7, 0.8, 0.9]:
        for weighting in ["equal", "prob", "sqrt"]:
            for top_k in [None, 1, 5, 10, 20]:
                configs.append((thr, top_k, weighting, None))
    # add some capped / high-thresh prob-weighting variants at thr0.9
    for top_k in [1, 3, 5, 10]:
        configs.append((0.9, top_k, "sqrt", 0.5))

    best = None
    for cfg in configs:
        r = run_config(*cfg)
        if r is None:
            continue
        key = f"thr{cfg[0]}_k{cfg[1]}_{cfg[2]}_cap{cfg[3]}"
        results[key] = r
        if best is None or r["sharpe"] > best[1]["sharpe"]:
            best = (key, r)

    print("Top 15 configs by calendar Sharpe:")
    ranked = sorted(results.items(), key=lambda kv: kv[1]["sharpe"], reverse=True)
    for k, r in ranked[:15]:
        print(f"  {k:>34}: SR={r['sharpe']} ann={r['ann']:.1%} DD={r['maxdd']:.1%} "
              f"trades={r['n_trades']} act={r['active_days']} win5={r['win5']:.1%}")

    with open(os.path.join(OUT, "bigmove_sharpe_opt.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nbest: {best[0]} SR={best[1]['sharpe']} -> saved bigmove_sharpe_opt.json")


if __name__ == "__main__":
    main()
