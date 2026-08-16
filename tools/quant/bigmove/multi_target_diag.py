"""Diagnose achievable precision across different 'huge return' target definitions.
Walks forward (quarterly refit, 3y window) training one model per target simult.
Targets:
  up5  : next-day return >= +5%   (long)
  up3  : next-day return >= +3%   (long, looser)
  abs5 : |next-day return| >= 5%  (either direction)
  down5: next-day return <= -5%   (short)
Reports precision (fraction of fired trades meeting the target) at prob thresholds
0.7 and 0.9, plus avg realized return. No look-ahead.
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
TRAIN_WIN = 252 * 3
REFIT = 63
START = "2018-01-01"
COST_ONE_SIDE = 0.00038


def main():
    P = load_ohlcv()
    close = P["close"]
    feats = build_features2(P)
    ret_next = close.pct_change().shift(-1)
    X_full, y_up5, rn, meta, _ = to_xy(feats, ret_next)
    rn = np.asarray(rn)   # flattened next-day returns aligned to X_full rows

    # build y for the other targets from the same flattened retnext
    targets = {
        "up5":   (rn >= 0.05).astype(int),
        "up3":   (rn >= 0.03).astype(int),
        "abs5":  (np.abs(rn) >= 0.05).astype(int),
        "down5": (rn <= -0.05).astype(int),
    }
    X_full = X_full.replace([np.inf, -np.inf], np.nan)

    dates = meta["date"].to_numpy()
    tickers = meta["ticker"].to_numpy()
    uniq_dates = np.unique(dates)
    start = pd.Timestamp(START)
    pred_dates = uniq_dates[uniq_dates >= np.datetime64(start)]
    refit_idx = np.arange(0, len(pred_dates), REFIT)

    probas = {t: np.full(len(X_full), np.nan) for t in targets}

    print(f"Refitting {len(refit_idx)}x for {len(targets)} targets...", flush=True)
    for k, kk in enumerate(refit_idx):
        d = pred_dates[kk]
        if k % 8 == 0:
            print(f"  [{k+1}/{len(refit_idx)}] {pd.Timestamp(d).date()}", flush=True)
        dmin = d - np.timedelta64(TRAIN_WIN, "D")
        tr = (dates < d) & (dates >= dmin)
        ok = np.isfinite(X_full.iloc[tr].to_numpy()).sum(axis=1) > 0
        Xtr = X_full.iloc[tr].iloc[ok]
        d_end = pred_dates[kk + REFIT] if kk + REFIT < len(pred_dates) \
            else pred_dates[-1] + np.timedelta64(1, "D")
        blk = (dates >= d) & (dates < d_end)
        Xb = X_full.iloc[blk]
        okb = np.isfinite(Xb.to_numpy()).sum(axis=1) > 0
        Xbk = Xb.iloc[okb]
        for t, y_all in targets.items():
            ytr = y_all[tr][ok]
            mdl = HistGradientBoostingClassifier(
                max_iter=250, learning_rate=0.05, max_depth=6, max_leaf_nodes=31,
                l2_regularization=1.0, class_weight="balanced",
                early_stopping=True, validation_fraction=0.1, n_iter_no_change=15,
                random_state=42)
            mdl.fit(Xtr, ytr)
            pb = np.full(len(Xb), np.nan)
            pb[okb] = mdl.predict_proba(Xbk)[:, 1]
            probas[t][blk] = pb

    meta_df = pd.DataFrame({"date": dates, "ticker": tickers, "retnext": rn})
    out = {"date": dates, "ticker": tickers, "rn": rn}
    for t in targets:
        out[f"p_{t}"] = probas[t]
    out = pd.DataFrame(out).dropna(subset=["rn"])

    results = {}
    for t in targets:
        pcol = f"p_{t}"
        d = out.dropna(subset=[pcol])
        for thr in [0.7, 0.9]:
            sel = d[d[pcol] >= thr]
            n = len(sel)
            if n == 0:
                results[f"{t}_thr{thr}"] = {"n": 0}; continue
            # precision = fraction meeting the target
            if t == "up5":  prec = (sel["rn"] >= 0.05).mean()
            elif t == "up3": prec = (sel["rn"] >= 0.03).mean()
            elif t == "abs5": prec = (np.abs(sel["rn"]) >= 0.05).mean()
            else: prec = (sel["rn"] <= -0.05).mean()
            avg_ret = sel["rn"].mean()   # signed realized return (favorable for target sign)
            results[f"{t}_thr{thr}"] = {"n": int(n), "precision": float(prec),
                                        "avg_ret": float(avg_ret)}
            print(f"target {t:>5} thr {thr:.1f}: {n:6,} trades | precision={prec:.2%} "
                  f"| avg signed ret={avg_ret:.4%}", flush=True)

    with open(os.path.join(OUT, "bigmove_multi_target_diag.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nsaved -> {OUT}/bigmove_multi_target_diag.json")


if __name__ == "__main__":
    main()
