"""Compare OLS vs GBRT vs GBRT+Gârleanu-Pedersen on real Polygon data.

Literature alignment:
  - GBRT  -> Gu, Kelly, Xiu (2020, RFS): empirical asset pricing via ML.
  - GP    -> Gârleanu & Pedersen (2013, JF): turnover-penalised dynamic
             portfolio choice with transaction costs.
  - 3.8 bps one-side / 7.6 bps round-trip = our actual retail commission.
  - Short-borrow cost applied daily to short market value (call-rate aware).

Run:
    python -m tools.quant.ls.run_gbrt_compare
"""
from __future__ import annotations
import os, sys, time, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
import numpy as np
from tools.quant.ls import Config, runner, experiment

# ---- shared base: mirror the current best OLS config (BEST_rev3_n13_vt20_38bps) ----
BASE = dict(
    data_dir="tools/quant/data/polygon",
    universe=(),
    benchmark="SPY",
    return_horizon_fwd=5,          # 20-day prediction horizon (Novy-Marx-Velikov sweet spot)
    return_type="log",
    factor_winsorize_p=0.01,
    factor_neutralize=["market"],
    factor_zscore=True,
    use_extra_factors=True,        # use the full 20+ factor set for GBRT
    icir_threshold=0.08,
    ic_mean_threshold=0.005,
    ic_sign_check=True,
    train_window=120,
    refit_freq=5,
    predict_horizon=5,             # 20-day = Novy-Marx-Velikov optimum at 7.6 bps RT
    n_long=10, n_short=10,
    use_fixed_n=True,
    weighting="mean_var",
    long_short_balance=True,
    beta_check=True,
    beta_target=0.0,
    beta_max_abs=0.15,
    position_cap_pct=0.25,
    vol_target_active=True,
    vol_target_annual=0.15,
    opt_method="scipy_slsqp",
    opt_lambda_risk=2.0,
    cost_bps_one_side=3.8,         # our actual commission
    cost_round_trip_bps=7.6,
    slippage_bps=1.0,
    rebalance_freq=5,
    turnover_threshold_diff=0.001,
    hold_to_reduce_turnover=True,
    hold_zone_top_pct_wide=0.05,
    hold_zone_bot_pct_wide=0.05,
    t_plus_1=True,
    gross_leverage=1.6,
    initial_capital=1_000_000,
    short_borrow_apply=True,       # call-rate / short-interest aware
    short_borrow_annual_bps=50.0,  # generic large-cap borrow
    short_borrow_htb_premium_bps=200.0,
    sharpe_gate_enabled=False,     # don't gate; we want all three for comparison
    diag_regime_split=True,
    save_intermediate=False,
    plot=False,
    verbose=False,
)

SPECS = [
    # 1) OLS baseline (current production method)
    ("ols_baseline", dict(model_method="ols", model_weight_smooth=0.3)),
    # 2) GBRT (Gu-Kelly-Xiu 2020) -- no turnover penalty yet
    ("gbrt_raw", dict(
        model_method="gbrt",
        gbrt_n_estimators=200,
        gbrt_max_depth=3,
        gbrt_learning_rate=0.05,
        gbrt_subsample=1.0,
        gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0,
        gbrt_pred_smooth=0.0,       # raw -- expect high churn
        gp_turnover_penalty=0.0,
        gp_no_trade_band=0.0,
    )),
    # 3) GBRT + Gârleanu-Pedersen (2013) turnover penalty + no-trade band
    ("gbrt_gp", dict(
        model_method="gbrt",
        gbrt_n_estimators=200,
        gbrt_max_depth=3,
        gbrt_learning_rate=0.05,
        gbrt_subsample=1.0,
        gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0,
        gbrt_pred_smooth=0.5,       # EMA-smooth predictions across refits
        gp_turnover_penalty=0.0038, # exact one-side commission per unit turnover
        gp_no_trade_band=0.01,      # 1% weight change -> skip
        gbrt_label_residual="none", # raw forward return
    )),
    # 4) GBRT + GP + Freyberger(2020) demeaned residual label
    ("gbrt_gp_demean", dict(
        model_method="gbrt",
        gbrt_n_estimators=200,
        gbrt_max_depth=3,
        gbrt_learning_rate=0.05,
        gbrt_subsample=1.0,
        gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0,
        gbrt_pred_smooth=0.5,
        gp_turnover_penalty=0.0038,
        gp_no_trade_band=0.01,
        gbrt_label_residual="demean",  # market-neutral label
        gbrt_label_winsorize=0.01,
    )),
    # 5) GBRT + GP + Freyberger(2020) PCA residual label (top-3 statistical factors)
    ("gbrt_gp_pca", dict(
        model_method="gbrt",
        gbrt_n_estimators=200,
        gbrt_max_depth=3,
        gbrt_learning_rate=0.05,
        gbrt_subsample=1.0,
        gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0,
        gbrt_pred_smooth=0.5,
        gp_turnover_penalty=0.0038,
        gp_no_trade_band=0.01,
        gbrt_label_residual="pca",   # regress out top-3 PCs
        gbrt_label_pca_n=3,
        gbrt_label_winsorize=0.01,
    )),
    # 6) Best-so-far (demean) + Huber loss (robust to fat-tailed returns)
    ("gbrt_gp_demean_huber", dict(
        model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=3, gbrt_learning_rate=0.05,
        gbrt_subsample=1.0, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        gbrt_loss="huber", gbrt_alpha=0.9,
        gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
        gp_turnover_penalty=0.0038, gp_no_trade_band=0.01,
        gbrt_label_residual="demean", gbrt_label_winsorize=0.01,
    )),
    # 7) Demean + z-score label (regime-stable)
    ("gbrt_gp_demean_zscore", dict(
        model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=3, gbrt_learning_rate=0.05,
        gbrt_subsample=1.0, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
        gp_turnover_penalty=0.0038, gp_no_trade_band=0.01,
        gbrt_label_residual="demean",
        gbrt_label_transform="zscore",
        gbrt_label_winsorize=0.01,
    )),
    # 8) Demean + rank label (GKX 2020 rank-IC objective)
    ("gbrt_gp_demean_rank", dict(
        model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=3, gbrt_learning_rate=0.05,
        gbrt_subsample=1.0, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
        gp_turnover_penalty=0.0038, gp_no_trade_band=0.01,
        gbrt_label_residual="demean",
        gbrt_label_transform="rank",
        gbrt_label_winsorize=0.01,
    )),
]

def main():
    out_dir = "tools/quant/ls/results/gbrt_compare"
    os.makedirs(out_dir, exist_ok=True)
    cfg0 = Config(out_dir=out_dir, name="compare", **BASE)
    rows = []
    for name, overrides in SPECS:
        cfg = cfg0.copy(name=name, **overrides)
        t0 = time.time()
        try:
            bundle = runner.run(cfg, export=False)
            m = bundle["metrics"]
            row = {
                "name": name,
                "model_method": cfg.model_method,
                "sharpe": round(m["sharpe"], 3),
                "annual_return": round(m["annual_return"], 4),
                "annual_vol": round(m["annual_volatility"], 4),
                "max_dd": round(m["max_drawdown"], 4),
                "annual_turnover": round(m["annual_turnover"], 2),
                "win_rate": round(m["win_rate"], 3),
                "avg_gross": round(m["avg_gross_exposure"], 3),
                "avg_abs_beta": round(m["avg_abs_beta"], 3),
                "final_equity": round(m["final_equity"], 0),
                "verdict": bundle["diagnostics"].get("verdict", {}).get("assessment", "?"),
                "n_flags": bundle["diagnostics"].get("verdict", {}).get("n_flags", "?"),
                "runtime_s": round(time.time() - t0, 1),
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            row = {"name": name, "status": f"error: {str(e)[:100]}", "runtime_s": round(time.time() - t0, 1)}
        rows.append(row)
        print(f"  done {name}: {row}")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "gbrt_compare.csv"), index=False)
    print("\n=== Comparison summary ===")
    print(df.to_string(index=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
