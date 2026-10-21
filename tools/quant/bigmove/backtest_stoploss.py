"""Backtest next-day >=5% strategy with configurable intraday STOP-LOSS exit.

Exit (next trading day T+1, using its OHLC bar):
  * if open(T+1) <= stop  -> exit at open(T+1)     (gap below stop)
  * elif low(T+1)  <= stop -> exit at stop         (intraday stop fill)
  * else                   -> exit at close(T+1)   (hold to close)
  stop = entry * (1 - stop_pct);  one-side cost 6 bps (12 bps round trip).

Efficiency: out-of-sample predictions (no look-ahead walk-forward) + the
flattened OHLC trade frame are CACHED to <bigmove>/data/pred_frame.parquet on
first run; subsequent runs (e.g. sweeping stop % levels) reuse the cache.
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
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "pred_frame.parquet")
os.makedirs(os.path.dirname(CACHE), exist_ok=True)
os.makedirs(OUT, exist_ok=True)

TRAIN_WIN = 252 * 3
REFIT = 63
COST_ONE_SIDE = 0.0006      # 6 bps one side
START = "2018-01-01"
TRADING_DAYS = 252
STOP_LEVELS = [0.01, 0.03, 0.05, 0.10]
THRESHOLDS = [0.7, 0.8, 0.9, 0.95]


def _stats(daily):
    s = (daily.mean() / daily.std()) * np.sqrt(TRADING_DAYS) if daily.std() > 0 else 0.0
    ann = (1 + daily).prod() ** (TRADING_DAYS / max(len(daily), 1)) - 1
    vol = daily.std() * np.sqrt(TRADING_DAYS)
    eq = np.cumprod(1 + daily)
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    return s, ann, vol, dd


def get_pred_frame(force=False):
    """Return cached trade frame {date,ticker,prob,entry_close,next_open,next_low,
    next_close,ret_no_stop}; generate if absent."""
    if os.path.exists(CACHE) and not force:
        return pd.read_parquet(CACHE)

    print("No cache -> computing walk-forward predictions...", flush=True)
    P = load_ohlcv()
    close, open_, low = P["close"], P["open"], P["low"]
    feats = build_features2(P)
    ret_next = close.pct_change().shift(-1)
    X_full, y_full, _, meta, _ = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf, -np.inf], np.nan)
    dates = meta["date"].to_numpy(); tickers = meta["ticker"].to_numpy()
    ud = np.unique(dates); start = pd.Timestamp(START)
    pd_ = ud[ud >= np.datetime64(start)]
    refit = np.arange(0, len(pd_), REFIT)
    print(f"OOS {pd.Timestamp(pd_[0]).date()}..{pd.Timestamp(pd_[-1]).date()} "
          f"| {len(refit)} refits", flush=True)
    prob = np.full(len(X_full), np.nan)
    for k, kk in enumerate(refit):
        if k % 8 == 0:
            print(f"  [{k+1}/{len(refit)}] refit @ {pd.Timestamp(pd_[kk]).date()}", flush=True)
        d = pd_[kk]; dmin = d - np.timedelta64(TRAIN_WIN, "D")
        tr = (dates < d) & (dates >= dmin)
        ok = np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1) > 0
        Xtr, ytr = X_full.iloc[tr].iloc[ok], y_full[tr][ok]
        m = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05,
            max_depth=6, max_leaf_nodes=31, l2_regularization=1.0,
            class_weight="balanced", early_stopping=True, validation_fraction=0.1,
            n_iter_no_change=15, random_state=42)
        m.fit(Xtr, ytr)
        d_end = pd_[kk + REFIT] if kk + REFIT < len(pd_) else pd_[-1] + np.timedelta64(1, "D")
        blk = (dates >= d) & (dates < d_end)
        Xb = X_full.iloc[blk]; okb = np.isfinite(Xb.to_numpy()).sum(axis=1) > 0
        pb = np.full(len(Xb), np.nan); pb[okb] = m.predict_proba(Xb.iloc[okb])[:, 1]
        prob[blk] = pb

    mi = pd.MultiIndex.from_arrays([dates, tickers], names=["date", "ticker"])
    def v(df, sh=0): return df.shift(sh).stack().reindex(mi).to_numpy()
    fr = pd.DataFrame({"date": dates, "ticker": tickers, "prob": prob,
                       "entry_close": v(close),
                       "next_open": v(open_, -1), "next_low": v(low, -1),
                       "next_close": v(close, -1)})
    fr = fr.dropna(subset=["prob", "entry_close", "next_open", "next_low", "next_close"])
    fr["ret_no_stop"] = fr["next_close"] / fr["entry_close"] - 1.0
    fr.to_parquet(CACHE)
    print(f"Cached {len(fr):,} rows -> {CACHE}", flush=True)
    return fr


def main():
    frame = get_pred_frame()
    print(f"\nTradeable obs: {len(frame):,}", flush=True)

    results = {}
    equity = {}
    for thr in THRESHOLDS:
        for sp in STOP_LEVELS:
            sel = frame[frame["prob"] >= thr]
            n = len(sel)
            key = f"thr{thr}_stop{int(sp*100)}"
            if n == 0:
                results[key] = {"n": 0, "stop_pct": sp}; continue
            entry = sel["entry_close"].to_numpy()
            stop = entry * (1 - sp)
            op, lo, cl = sel["next_open"].to_numpy(), sel["next_low"].to_numpy(), sel["next_close"].to_numpy()
            exit_px = np.where(op <= stop, op, np.where(lo <= stop, stop, cl))
            reason = np.where(op <= stop, "open", np.where(lo <= stop, "stop", "close"))
            gross = exit_px / entry - 1.0
            net = gross - 2 * COST_ONE_SIDE
            d = pd.DataFrame({"date": sel["date"].to_numpy(), "net": net})
            dret = d.groupby("date")["net"].mean()
            s, ann, vol, dd = _stats(dret)
            results[key] = {
                "n": int(n), "days": int(dret.size),
                "hit5": round(float((gross >= 0.05).mean()), 4),
                "avg_gross": round(float(gross.mean()), 5),
                "avg_net": round(float(net.mean()), 5),
                "daily_sharpe": round(float(s), 3),
                "ann_return": round(float(ann), 4),
                "max_dd": round(float(dd), 4),
                "exit_open": round(float((reason == "open").mean()), 4),
                "exit_stop": round(float((reason == "stop").mean()), 4),
                "exit_close": round(float((reason == "close").mean()), 4),
            }
            equity[key] = pd.Series(np.cumprod(1 + dret), index=dret.index)
            print(f"\n===== thr>={thr} stop={sp:.0%} =====", flush=True)
            print(f"  {n:,} trades/{dret.size} days | hit5={results[key]['hit5']:.2%} "
                  f"| net/trade={net.mean():.4%}", flush=True)
            print(f"  exits open/stop/close = "
                  f"{results[key]['exit_open']:.1%}/{results[key]['exit_stop']:.1%}/"
                  f"{results[key]['exit_close']:.1%}", flush=True)
            print(f"  daily-EW Sharpe {s:.2f} | ann {ann:.2%} | maxDD {dd:.2%}", flush=True)

    with open(os.path.join(OUT, "bigmove_stoploss_results.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    pd.DataFrame(equity).to_csv(os.path.join(OUT, "bigmove_stoploss_equity.csv"))
    print(f"\nsaved -> {OUT}/bigmove_stoploss_results.json + bigmove_stoploss_equity.csv", flush=True)


if __name__ == "__main__":
    main()
