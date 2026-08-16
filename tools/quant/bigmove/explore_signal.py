"""Initial signal check: is there any predictive power at all for next-day >=5%?

Time-ordered split: train on the EARLIER years, evaluate on the LATER years.
No look-ahead (features at T use bars <=T; target uses T->T+1).
Reports ROC-AUC, precision at probability thresholds, and how many trades
would have fired at the 70% threshold.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss

from pipeline_common import load_ohlcv
from features import build_features, to_xy

CUT1 = "2020-01-01"   # train data before this
CUT2 = "2024-01-01"   # validation / test start


def main():
    print("Loading data...")
    P = load_ohlcv()
    close = P["close"]
    print(f"Panel: {close.shape[1]} tickers x {close.shape[0]} days "
          f"({close.index.min().date()}..{close.index.max().date()})")

    print("Building features...")
    feats = build_features(P)
    print(f"  {len(feats)} feature families")

    # next-day return target (aligned so row T = return T->T+1)
    ret_next = close.pct_change().shift(-1)

    # build X/y for the full range (features valid from MIN_HISTORY onward)
    X_full, y_full, retnext, meta, names = to_xy(feats, ret_next)
    print(f"Full X shape: {X_full.shape}, {len(X_full):,} stock-days")
    print(f"  positive rate (>=5% next day): {y_full.mean():.4%}")

    # drop infinite values
    X_full = X_full.replace([np.inf, -np.inf], np.nan)

    # time split masks (positional numpy masks over flattened rows)
    dates = meta["date"].to_numpy()
    tr_mask = dates < np.datetime64(CUT1)
    va_mask = (dates >= np.datetime64(CUT1)) & (dates < np.datetime64(CUT2))
    te_mask = dates >= np.datetime64(CUT2)

    Xtr, ytr = X_full.iloc[tr_mask], y_full[tr_mask]
    Xte, yte = X_full.iloc[te_mask], y_full[te_mask]
    Xva, yva = X_full.iloc[va_mask], y_full[va_mask]
    print(f"\nTrain: {Xtr.shape[0]:,} rows (pos {ytr.mean():.4%})")
    print(f"Val  : {Xva.shape[0]:,} rows (pos {yva.mean():.4%})")
    print(f"Test : {Xte.shape[0]:,} rows (pos {yte.mean():.4%})")

    print("\nTraining HistGradientBoosting (class-weighted)...")
    model = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.05, max_depth=5,
        max_leaf_nodes=31, l2_regularization=1.0,
        class_weight="balanced",
        early_stopping=True, validation_fraction=0.1, n_iter_no_change=30,
        random_state=42,
    )
    model.fit(Xtr, ytr)

    for split_name, X, y in [("Val", Xva, yva), ("Test", Xte, yte)]:
        proba = model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, proba)
        print(f"\n===== {split_name} split =====")
        print(f"  ROC-AUC: {auc:.4f}")
        # precision at thresholds
        for thr in [0.3, 0.5, 0.6, 0.7, 0.8, 0.9]:
            pred = proba >= thr
            if pred.sum() == 0:
                print(f"  thr {thr:.1f}: no trades fired")
                continue
            prec = y[pred].mean()
            n_trades = int(pred.sum())
            print(f"  thr {thr:.1f}: {n_trades:6,} trades | precision={prec:.2%}")

    # Save the model + feature names for the backtest script
    import joblib
    os.makedirs(os.path.join(os.path.dirname(__file__), "models"), exist_ok=True)
    joblib.dump({"model": model, "names": names},
                os.path.join(os.path.dirname(__file__), "models", "explore_model.joblib"))
    print("\nsaved model -> bigmove/models/explore_model.joblib")


if __name__ == "__main__":
    main()
