"""Honest walk-forward backtest for the next-day big-move strategy.

Rules:
  * Universe: US large caps from twelve_big panel, excl. blocklist.
  * Signal: gradient-boosted probability P(next-day return over close(T)->close(T+1) >= 5%),
    computed ONLY from bars <= T (no look-ahead).
  * Model rolled forward: retrain on a rolling 3-year window once per quarter,
    predict the following quarter's daily signals.
  * Trade: on day T, if predicted prob >= threshold, go LONG at close(T), exit at
    close(T+1) (realized next-day return). Net of round-trip cost.
  * Portfolio: equal notional per signal fired on a day; aggregate all same-day
    signals into a daily portfolio return -> daily equity curve, Sharpe, maxDD.
  * Report hit-rate at >=5% and average per-trade return at each threshold.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from pipeline_common import load_ohlcv
from features2 import build_features2
from features import to_xy

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports")
os.makedirs(OUT, exist_ok=True)

TRAIN_WIN = 252 * 3        # 3-year rolling training window
REFIT = 63                 # refit quarterly (63 trading days)
COST_ONE_SIDE = 0.00038    # 3.8 bps one side
START = "2018-01-01"       # start of out-of-sample backtest
TRADING_DAYS = 252


def _stats(daily):
    s = (daily.mean() / daily.std()) * np.sqrt(TRADING_DAYS) if daily.std() > 0 else 0.0
    ann = (1 + daily).prod() ** (TRADING_DAYS / max(len(daily), 1)) - 1
    vol = daily.std() * np.sqrt(TRADING_DAYS)
    eq = np.cumprod(1 + daily)
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    return s, ann, vol, dd


def main():
    print("Loading data...", flush=True)
    P = load_ohlcv()
    close = P["close"]
    print(f"Panel: {close.shape[1]} tickers x {close.shape[0]} days "
          f"({close.index.min().date()}..{close.index.max().date()})", flush=True)

    feats = build_features2(P)
    ret_next = close.pct_change().shift(-1)
    X_full, y_full, retnext, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf, -np.inf], np.nan)
    print(f"  {len(feats)} features | {len(X_full):,} stock-days | pos {y_full.mean():.2%}",
          flush=True)

    dates = meta["date"].to_numpy()
    tickers = meta["ticker"].to_numpy()
    uniq_dates = np.unique(dates)
    start = pd.Timestamp(START)
    pred_dates = uniq_dates[uniq_dates >= np.datetime64(start)]
    print(f"Out-of-sample: {pd.Timestamp(pred_dates[0]).date()} .. "
          f"{pd.Timestamp(pred_dates[-1]).date()} ({len(pred_dates)} days)", flush=True)

    pred_proba = np.full(len(X_full), np.nan)

    refit_idx = np.arange(0, len(pred_dates), REFIT)
    print(f"Refitting {len(refit_idx)} times (quarterly)", flush=True)
    for k, kk in enumerate(refit_idx):
        d = pred_dates[kk]
        print(f"  [{k+1}/{len(refit_idx)}] refit @ {pd.Timestamp(d).date()}", flush=True)
        dmin = d - np.timedelta64(TRAIN_WIN, "D")
        tr = (dates < d) & (dates >= dmin)
        Xtr = X_full.iloc[tr]
        ytr = y_full[tr]
        ok = np.isfinite(Xtr.to_numpy()).sum(axis=1) > 0
        Xtr, ytr = Xtr.iloc[ok], ytr[ok]
        mdl = HistGradientBoostingClassifier(
            max_iter=350, learning_rate=0.05, max_depth=6, max_leaf_nodes=31,
            l2_regularization=1.0, class_weight="balanced",
            early_stopping=True, validation_fraction=0.1, n_iter_no_change=20,
            random_state=42)
        mdl.fit(Xtr, ytr)
        d_end = pred_dates[kk + REFIT] if kk + REFIT < len(pred_dates) \
            else pred_dates[-1] + np.timedelta64(1, "D")
        blk = (dates >= d) & (dates < d_end)
        Xb = X_full.iloc[blk]
        okb = np.isfinite(Xb.to_numpy()).sum(axis=1) > 0
        pb = np.full(len(Xb), np.nan)
        pb[okb] = mdl.predict_proba(Xb.iloc[okb])[:, 1]
        pred_proba[blk] = pb

    out = pd.DataFrame({"date": dates, "ticker": tickers, "prob": pred_proba,
                        "retnext": retnext, "target": y_full})
    out = out.dropna(subset=["prob", "retnext"])
    print(f"\nOut-of-sample predictions: {len(out):,} stock-days", flush=True)

    # ---------------- trading across thresholds ----------------
    summary = {}
    equity_curves = {}
    for thr in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        trades = out[out["prob"] >= thr].copy()
        n = len(trades)
        if n == 0:
            summary[str(thr)] = {"n": 0}; continue
        trades["net"] = trades["retnext"] - 2 * COST_ONE_SIDE
        hit = (trades["retnext"] >= 0.05).mean()
        avg_gross = trades["retnext"].mean()
        avg_net = trades["net"].mean()
        # daily portfolio return: equal-weight all signals on a given date
        dret = trades.groupby("date")["net"].mean()
        s, ann, vol, dd = _stats(dret)
        # per-trade notional compounding is not meaningful across unequal signals/day;
        # we report the daily-equal-weighted book + its stats.
        total = dret.sum()   # approx total return (sum of daily EW returns)
        # also count distinct days
        ndays = dret.size
        summary[str(thr)] = {
            "n": int(n), "n_signals_by_day": f"{ndays} days (~{n/ndays:.1f} signals/day)",
            "hit_gte5": float(hit), "avg_gross": float(avg_gross),
            "avg_net": float(avg_net), "daily_sharpe": round(float(s), 3),
            "ann_return": round(float(ann), 4), "ann_vol": round(float(vol), 4),
            "max_dd": round(float(dd), 4), "total_dret_sum": round(float(total), 4),
        }
        equity_curves[str(thr)] = pd.Series(np.cumprod(1 + dret), index=dret.index)
        print(f"\n===== threshold >= {thr} =====", flush=True)
        print(f"  trades: {n:,} over {ndays} days (~{n/ndays:.1f} signals/day)", flush=True)
        print(f"  hit rate (>=5%): {hit:.2%}", flush=True)
        print(f"  avg gross/trade: {avg_gross:.4%} | avg net: {avg_net:.4%}", flush=True)
        print(f"  daily EW book: Sharpe {s:.2f} | Ann {ann:.2%} | MaxDD {dd:.2%}", flush=True)

    # save
    with open(os.path.join(OUT, "bigmove_walkforward_results.json"), "w") as f:
        json.dump(summary, f, indent=2, default=str)
    pd.DataFrame(equity_curves).to_csv(os.path.join(OUT, "bigmove_equity_by_threshold.csv"))
    print(f"\nsaved -> {OUT}/bigmove_walkforward_results.json , bigmove_equity_by_threshold.csv",
          flush=True)


if __name__ == "__main__":
    main()
