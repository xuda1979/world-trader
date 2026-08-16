"""Full backtest of the XGBoost REGRESSION model (best signal).

Engine: XGBRegressor predicts next-day return; we buy the highest-predicted
names. Includes the user's intraday stop-loss exit (6bp one-side):
  * if next open <= stop -> exit at open
  * elif next low  <= stop -> exit at stop
  * else -> exit at next close
where stop = entry*(1-stop%). No look-ahead (signals from cached walk-forward).
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from pipeline_common import load_ohlcv

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports")
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "xgb_pred_frame.parquet")
COST = 0.0006
TRADING_DAYS = 252

fr = pd.read_parquet(CACHE)
fr["date"] = pd.to_datetime(fr["date"])

# ---- attach next-day OHLC (open/low) for the exit rule ----
P = load_ohlcv()
open_, low, close = P["open"], P["low"], P["close"]

# for each (date,ticker) row, get next-day open/low via shift(-1) per ticker
mi = pd.MultiIndex.from_arrays([fr["date"].to_numpy(), fr["ticker"].to_numpy()],
                               names=["date", "ticker"])
def vec(df, sh=0):
    return df.shift(sh).stack().reindex(mi).to_numpy()

fr["next_open"] = vec(open_, -1)
fr["next_low"] = vec(low, -1)
# sanity check alignment: no-stop rn should equal next_close/entry - 1
fr["rn_check"] = fr["next_close"] / fr["entry"] - 1.0
mismatch = (fr["rn"] - fr["rn_check"]).abs().max()
print(f"alignment check: max |rn - next/entry-1| = {mismatch:.2e}")
fr = fr.dropna(subset=["next_open", "next_low"])


def exit_logic(entry, op, lo, cl, stop_pct):
    stop = entry * (1 - stop_pct)
    exit_px = np.where(op <= stop, op, np.where(lo <= stop, stop, cl))
    reason = np.where(op <= stop, "open", np.where(lo <= stop, "stop", "close"))
    gross = exit_px / entry - 1.0
    net = gross - 2 * COST
    return gross, net, reason, stop


def stats_calendar(daily):
    if daily.std() == 0: return 0.0, 0.0, 0.0
    s = (daily.mean()/daily.std())*np.sqrt(TRADING_DAYS)
    ann = (1+daily).prod()**(TRADING_DAYS/len(daily))-1
    eq = (1+daily).cumprod(); dd = (eq/eq.cummax()-1).min()
    return s, ann, dd


def run(d, stop_pct, weight_by):
    """Portfolio: on each day, go long the selected names; returns daily series."""
    d = d.copy()
    entry = d["entry"].to_numpy(); op = d["next_open"].to_numpy()
    lo = d["next_low"].to_numpy(); cl = d["next_close"].to_numpy()
    gross, net, reason, stop = exit_logic(entry, op, lo, cl, stop_pct)
    # weights
    if weight_by == "pred":
        w = np.abs(d["pred_ret"].to_numpy()).clip(0.001, None)
    else:
        w = np.ones(len(d))
    wsum = pd.Series(w, index=d.index).groupby(d["date"]).transform("sum")
    alloc = w / wsum.to_numpy()
    d["alloc"] = alloc; d["net"] = net * alloc
    daily = d.groupby("date")["net"].sum()
    cal = daily.reindex(fr["date"].unique(), fill_value=0).sort_index()
    s, ann, dd = stats_calendar(cal)
    win5 = (gross >= 0.05).mean()
    return {"cal_sharpe": round(s,3), "ann": round(ann,4), "maxdd": round(float(dd),4),
            "n": int(len(d)), "days": int(daily.size),
            "win5": round(float(win5),4), "avg_net": round(float(net.mean()),5),
            "perT_SR": round(float(net.mean()/net.std()),3) if net.std()>0 else 0,
            "exit_open": round(float((reason=="open").mean()),4),
            "exit_stop": round(float((reason=="stop").mean()),4),
            "exit_close": round(float((reason=="close").mean()),4),
            "avg_sig_day": round(len(d)/max(len(daily),1),2)}


def main():
    live = fr[fr["pred_ret"].notna()].copy()
    print(f"tradeable obs: {len(live):,}\n")

    results = {}
    print("=== XGB regression backtest (calendar-time, 6bp one-side) ===")
    for q in [0.99, 0.995, 0.997, 0.999]:
        cut = live["pred_ret"].quantile(q)
        d = live[live["pred_ret"] >= cut]
        if len(d) == 0: continue
        for stop_pct in [0.0, 0.01, 0.05, 0.10]:
            for wgt in ["equal", "pred"]:
                key = f"top{1-q:.3f}_stop{int(stop_pct*100)}_w{wgt}"
                r = run(d, stop_pct, wgt)
                results[key] = r
                print(f"  {key:>28}: SR={r['cal_sharpe']} ann={r['ann']:.1%} DD={r['maxdd']:.0%} "
                      f"n={r['n']:5,} win5={r['win5']:.1%} net={r['avg_net']:+.4%} "
                      f"O/S/C={r['exit_open']:.0%}/{r['exit_stop']:.0%}/{r['exit_close']:.0%}")

    # ---- block-bootstrap significance on the no-stop top buckets ----
    print("\n=== robustness (date-block bootstrap) ===")
    for q in [0.995, 0.997]:
        cut = live["pred_ret"].quantile(q)
        d = live[live["pred_ret"] >= cut]
        gross, net, reason, stop = exit_logic(d["entry"].to_numpy(), d["next_open"].to_numpy(),
                                              d["next_low"].to_numpy(), d["next_close"].to_numpy(), 0.0)
        daily = pd.Series(net, index=d["date"].to_numpy()).groupby(level=0).mean()
        arr = daily.to_numpy(); di = len(arr); blk = 10
        rng = np.random.default_rng(0)
        nb = di // blk
        samp = np.array([arr[rng.integers(0, di-blk, size=nb)[:, None] + np.arange(blk)[None, :]].ravel().mean()
                         for _ in range(3000)])
        ci = np.percentile(samp, [2.5, 97.5])
        t, p = stats.ttest_1samp(net, 0)
        print(f"  top{1-q:.1%}: n={len(net)} unique_days={len(d['date'].unique())} "
              f"naive_t={t:.2f} naive_p={p:.3f} | block95CI=[{ci[0]:.4f},{ci[1]:.4f}] "
              f"{'SIG' if ci[0]>0 else 'NOT-SIG'}")

    with open(os.path.join(OUT, "bigmove_xgb_backtest.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nsaved -> {OUT}/bigmove_xgb_backtest.json")


if __name__ == "__main__":
    main()
