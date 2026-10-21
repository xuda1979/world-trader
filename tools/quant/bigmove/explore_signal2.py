"""Signal check with ENHANCED features: does precision improve toward 70%?
Same time-ordered split as explore_signal.py."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.calibration import calibration_curve

from pipeline_common import load_ohlcv
from features2 import build_features2
from features import to_xy

CUT1 = "2020-01-01"
CUT2 = "2024-01-01"


def main():
    print("Loading data...")
    P = load_ohlcv()
    close = P["close"]
    feats = build_features2(P)
    print(f"  {len(feats)} feature families")
    ret_next = close.pct_change().shift(-1)
    X_full, y_full, retnext, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf, -np.inf], np.nan)
    print(f"Full X: {X_full.shape}, pos rate {y_full.mean():.4%}")

    dates = meta["date"].to_numpy()
    tr_mask = dates < np.datetime64(CUT1)
    te_mask = dates >= np.datetime64(CUT2)
    va_mask = (dates >= np.datetime64(CUT1)) & (dates < np.datetime64(CUT2))

    Xtr, ytr = X_full.iloc[tr_mask], y_full[tr_mask]
    Xte, yte = X_full.iloc[te_mask], y_full[te_mask]
    Xva, yva = X_full.iloc[va_mask], y_full[va_mask]

    print("Training enhanced-feature model...")
    model = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.05, max_depth=6, max_leaf_nodes=31,
        l2_regularization=1.0, class_weight="balanced",
        early_stopping=True, validation_fraction=0.1, n_iter_no_change=30,
        random_state=42)
    model.fit(Xtr, ytr)

    for split_name, X, y in [("Val", Xva, yva), ("Test", Xte, yte)]:
        proba = model.predict_proba(X)[:, 1]
        auc = roc_auc_score(y, proba)
        print(f"\n===== {split_name} split (enhanced feats) AUC={auc:.4f} =====")
        for thr in [0.5, 0.6, 0.7, 0.8, 0.9]:
            pred = proba >= thr
            n = int(pred.sum())
            if n == 0:
                print(f"  thr {thr:.1f}: no trades"); continue
            print(f"  thr {thr:.1f}: {n:6,} trades | precision={y[pred].mean():.2%}")
        # calibration curve at 10 bins
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                fop, mpp = calibration_curve(y, proba, n_bins=10, strategy="quantile")
                # print mean predicted prob per bin vs actual freq
                print("  calibration (predicted vs actual freq):")
                for mp, fo in zip(mpp, fop):
                    if mp > 0.5:
                        print(f"    pred~{mp:.2f} : actual {fo:.2%}")
            except Exception as e:
                print("  calibration err", e)

if __name__ == "__main__":
    main()
