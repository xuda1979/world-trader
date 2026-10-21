"""RF hyperparameter sweep: depth x n_estimators x pred_smooth x screen.

RF (rf_d8_n500_bypass) hit Sharpe 0.984 with watch verdict -- best non-GBRT model.
This sweep explores the RF hyperplane to find the best configuration.

Two screen modes tested:
  A. bypass_ic_screen=True  -- all ~33 factors go to RF (RF does feature sel.)
  B. icir_threshold=0.15    -- keep ~8 quality factors (cleaner signal)
"""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from tools.quant.ls.runner import run_sweep
from tools.quant.ls.config import Config

BASE = dict(
    model_method="rf",
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
    icir_threshold=0.30, ic_mean_threshold=0.005,
    gbrt_label_transform="zscore", gbrt_label_residual="demean",
    gbrt_label_winsorize=0.01, gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    rf_max_depth=8, rf_n_estimators=500, rf_min_samples_leaf=15,
    rf_max_features="sqrt",
    diag_window_sweep=(100, 120, 140), diag_regime_split=True,
    out_dir="tools/quant/ls/results",
    save_intermediate=True, plot=False, verbose=False,
)

def main():
    cfg = Config(**BASE)
    print("=" * 60)
    print("PHASE 1: RF depth x n_estimators (bypass, smooth=0.5, leaf=15)")
    print("=" * 60)
    df1 = run_sweep(cfg, {
        "rf_max_depth": [4, 6, 8, 10],
        "rf_n_estimators": [200, 500, 1000],
    })
    df1.to_csv(os.path.join(ROOT, cfg.out_dir, "rf_sweep_phase1.csv"), index=False)
    cols = ["name","sharpe","annual_return","max_drawdown","annual_turnover","verdict"]
    print(df1[[c for c in cols if c in df1.columns]].to_string())
    best_depth = int(df1.loc[df1["sharpe"].idxmax(), "rf_max_depth"]) if "sharpe" in df1.columns and len(df1) else 8
    best_nest = int(df1.loc[df1["sharpe"].idxmax(), "rf_n_estimators"]) if "sharpe" in df1.columns and len(df1) else 500
    print(f"Best P1: depth={best_depth}, n_est={best_nest}")
    print()
    print("=" * 60)
    print(f"PHASE 2: min_leaf x pred_smooth (bypass, depth={best_depth}, n_est={best_nest})")
    print("=" * 60)
    cfg2 = cfg.copy(rf_max_depth=best_depth, rf_n_estimators=best_nest)
    df2 = run_sweep(cfg2, {
        "rf_min_samples_leaf": [10, 20, 30, 50],
        "gbrt_pred_smooth": [0.3, 0.5, 0.7],
    })
    df2.to_csv(os.path.join(ROOT, cfg.out_dir, "rf_sweep_phase2.csv"), index=False)
    print(df2[[c for c in cols if c in df2.columns]].to_string())
    best_leaf = int(df2.loc[df2["sharpe"].idxmax(), "rf_min_samples_leaf"]) if "sharpe" in df2.columns and len(df2) else 20
    best_smooth = float(df2.loc[df2["sharpe"].idxmax(), "gbrt_pred_smooth"]) if "sharpe" in df2.columns and len(df2) else 0.5
    print()
    print("=" * 60)
    print("PHASE 3: RF with ICIR threshold=0.15 (keeps ~8 factors)")
    print("=" * 60)
    cfg3 = Config(**{**BASE,
        "rf_max_depth": best_depth, "rf_n_estimators": best_nest,
        "rf_min_samples_leaf": best_leaf, "gbrt_pred_smooth": best_smooth,
        "bypass_ic_screen": False, "icir_threshold": 0.15,
        "ic_bonferroni": False,
    })
    df3 = run_sweep(cfg3, {
        "rf_max_depth": [4, 6, 8],
        "rf_n_estimators": [200, 500],
        "gbrt_pred_smooth": [0.3, 0.5],
    })
    df3.to_csv(os.path.join(ROOT, cfg.out_dir, "rf_sweep_phase3.csv"), index=False)
    print(df3[[c for c in cols if c in df3.columns]].to_string())
    print()
    print("=== RF sweep complete ===")

if __name__ == "__main__":
    main()
