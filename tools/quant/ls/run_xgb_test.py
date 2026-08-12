"""XGBoost test sweep.

XGBoost (Chen & Guestrin 2016) typically outperforms GBRT and RF on tabular
data due to better regularization (L1+L2) and more sophisticated tree pruning.
"""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from tools.quant.ls.runner import run_sweep
from tools.quant.ls.config import Config

BASE = dict(
    model_method="xgb",
    predict_horizon=10, return_horizon_fwd=10,
    rebalance_freq=10, refit_freq=10, train_window=120,
    n_long=10, n_short=10,
    weighting="mean_var", opt_lambda_risk=0.5,
    position_cap_pct=0.20, gross_leverage=1.6, max_gross_leverage=1.6,
    vol_target_active=False,
    cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
    use_call_rate_financing=True, long_financing_apply=True,
    short_rebate_paid_bps=150.0, short_borrow_fee_etb_bps=25.0,
    long_financing_spread_bps=50.0,
    use_extra_factors=True, use_ohlc_factors=True,
    use_interaction_features=False,
    bypass_ic_screen=True,
    gbrt_label_transform="zscore", gbrt_label_residual="demean",
    gbrt_label_winsorize=0.01, gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    xgb_max_depth=3, xgb_n_estimators=200, xgb_learning_rate=0.05,
    xgb_subsample=0.8, xgb_colsample_bytree=0.8,
    xgb_reg_alpha=0.1, xgb_reg_lambda=1.0, xgb_min_child_weight=5,
    diag_window_sweep=(100, 120, 140), diag_regime_split=True,
    out_dir="tools/quant/ls/results",
    save_intermediate=True, plot=False, verbose=False,
)

def main():
    cfg = Config(**BASE)
    cols = ["name","sharpe","annual_return","max_drawdown","annual_turnover","verdict"]

    print("=" * 60)
    print("XGB PHASE 1: depth x n_estimators (bypass, smooth=0.5)")
    print("=" * 60)
    df1 = run_sweep(cfg, {
        "xgb_max_depth": [2, 3, 4, 5],
        "xgb_n_estimators": [100, 200, 500],
    })
    df1.to_csv(os.path.join(ROOT, cfg.out_dir, "xgb_sweep_phase1.csv"), index=False)
    print(df1[[c for c in cols if c in df1.columns]].to_string())
    if "sharpe" in df1.columns and len(df1) > 0:
        best_depth = int(df1.loc[df1["sharpe"].idxmax(), "xgb_max_depth"])
        best_nest = int(df1.loc[df1["sharpe"].idxmax(), "xgb_n_estimators"])
    else:
        best_depth, best_nest = 3, 200
    print(f"Best P1: depth={best_depth}, n_est={best_nest}")

    print()
    print("=" * 60)
    print(f"XGB PHASE 2: pred_smooth x learning_rate (depth={best_depth}, n_est={best_nest})")
    print("=" * 60)
    cfg2 = cfg.copy(xgb_max_depth=best_depth, xgb_n_estimators=best_nest)
    df2 = run_sweep(cfg2, {
        "gbrt_pred_smooth": [0.3, 0.5, 0.7],
        "xgb_learning_rate": [0.03, 0.05, 0.10],
    })
    df2.to_csv(os.path.join(ROOT, cfg.out_dir, "xgb_sweep_phase2.csv"), index=False)
    print(df2[[c for c in cols if c in df2.columns]].to_string())

    print()
    print("=" * 60)
    print("XGB PHASE 3: with ICIR threshold=0.15")
    print("=" * 60)
    cfg3 = cfg.copy(
        xgb_max_depth=best_depth, xgb_n_estimators=best_nest,
        bypass_ic_screen=False, icir_threshold=0.15,
        ic_bonferroni=False, ic_mean_threshold=0.005,
    )
    df3 = run_sweep(cfg3, {
        "xgb_max_depth": [2, 3, 4, 5],
        "xgb_n_estimators": [100, 200, 500],
        "gbrt_pred_smooth": [0.3, 0.5],
    })
    df3.to_csv(os.path.join(ROOT, cfg.out_dir, "xgb_sweep_phase3.csv"), index=False)
    print(df3[[c for c in cols if c in df3.columns]].to_string())
    print()
    print("=== XGB sweep complete ===")

if __name__ == "__main__":
    main()
