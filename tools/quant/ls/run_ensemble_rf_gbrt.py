"""Ensemble: GBRT (h=10, d=2) + RF (bypass, varied depth) + horizons.

Combines the two best model families:
  - GBRT h=10 d=2: Sharpe 1.237 (clean repro confirmed)
  - RF bypass: Sharpe 0.984 (d=8), 0.986 (d=6)
  - GBRT h=5 d=2: Sharpe 0.784 (diversifying horizon)

Build ensemble portfolios using mean-variance, equal-weight, risk-parity,
and min-variance optimization methods.
"""
import os, sys, json
import numpy as np
import pandas as pd
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

BASE = dict(
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
    gbrt_label_transform="zscore", gbrt_label_residual="demean",
    gbrt_label_winsorize=0.01, gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    diag_window_sweep=(100, 120, 140), diag_regime_split=True,
    out_dir="tools/quant/ls/results",
    save_intermediate=False, plot=False, verbose=False,
)

# Define strategies to run
strategies = [
    # Best GBRT
    ("gbrt_h10_d2", dict(
        model_method="gbrt", gbrt_max_depth=2, gbrt_n_estimators=200,
        gbrt_learning_rate=0.05, gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt", gbrt_subsample=1.0,
        predict_horizon=10,
        bypass_ic_screen=False, icir_threshold=0.08,
        ic_bonferroni=True, ic_mean_threshold=0.02,
        use_extra_factors=False, use_ohlc_factors=False,
        refit_freq=5,
    )),
    # GBRT with bypass (all 33 factors)
    ("gbrt_h10_d2_bypass", dict(
        model_method="gbrt", gbrt_max_depth=2, gbrt_n_estimators=200,
        gbrt_learning_rate=0.05, gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt",
        predict_horizon=10,
        bypass_ic_screen=True,
        use_extra_factors=True, use_ohlc_factors=True,
        refit_freq=5,
    )),
    # RF bypass d=6
    ("rf_h10_d6_bypass", dict(
        model_method="rf", rf_max_depth=6, rf_n_estimators=200,
        rf_min_samples_leaf=20, rf_max_features="sqrt",
        predict_horizon=10,
        bypass_ic_screen=True,
        use_extra_factors=True, use_ohlc_factors=True,
    )),
    # RF bypass d=8
    ("rf_h10_d8_bypass", dict(
        model_method="rf", rf_max_depth=8, rf_n_estimators=500,
        rf_min_samples_leaf=15, rf_max_features="sqrt",
        predict_horizon=10,
        bypass_ic_screen=True,
        use_extra_factors=True, use_ohlc_factors=True,
    )),
    # GBRT h=5 (diversifying horizon)
    ("gbrt_h5_d2", dict(
        model_method="gbrt", gbrt_max_depth=2, gbrt_n_estimators=200,
        gbrt_learning_rate=0.05, gbrt_min_samples_leaf=20,
        gbrt_max_features="sqrt", gbrt_subsample=1.0,
        predict_horizon=5, return_horizon_fwd=5,
        rebalance_freq=5, refit_freq=5,
        bypass_ic_screen=False, icir_threshold=0.08,
        ic_bonferroni=True, ic_mean_threshold=0.02,
        use_extra_factors=False, use_ohlc_factors=False,
    )),
]

out_dir = os.path.join(ROOT, "tools/quant/ls/results/ensemble_rf_gbrt")
os.makedirs(out_dir, exist_ok=True)

# Run each strategy
results = {}
daily_returns = {}
for i, (name, overrides) in enumerate(strategies):
    cfg_dict = dict(BASE, name=name, **overrides)
    cfg_dict["out_dir"] = os.path.join(out_dir, name)
    cfg = Config.from_dict(cfg_dict)
    print(f"[{i+1}/{len(strategies)}] Running {name}...")
    sys.stdout.flush()
    try:
        bundle = runner.run(cfg, export=True)
        m = bundle["metrics"]
        v = bundle["diagnostics"]["verdict"]
        results[name] = dict(
            sharpe=m.get("sharpe", 0), ann_ret=m.get("annual_return", 0),
            turnover=m.get("annual_turnover", 0), max_dd=m.get("max_drawdown", 0),
            ann_vol=m.get("annual_volatility", 0), verdict=v["assessment"],
            n_flags=v["n_flags"], n_factors=len(bundle.get("kept_factors", [])),
        )
        # Daily returns for ensemble building
        daily_ret = bundle["result"]["daily_returns"]
        if not daily_ret.empty:
            daily_returns[name] = daily_ret.iloc[:, 0]  # equity curve returns
        print(f"  Sharpe={results[name]['sharpe']:.3f}  ret={results[name]['ann_ret']:.3f}  "
              f"TO={results[name]['turnover']:.1f}  DD={results[name]['max_dd']:.3f}  "
              f"{results[name]['verdict']}({results[name]['n_flags']})")
    except Exception as e:
        import traceback; traceback.print_exc()
        results[name] = dict(error=str(e))
    sys.stdout.flush()

# Build ensemble from collected daily returns
if len(daily_returns) >= 2:
    print(f"
=== Building ensemble from {len(daily_returns)} strategies ===")
    ret_df = pd.DataFrame(daily_returns).dropna()
    ret_df.index = pd.to_datetime(ret_df.index)

    # Correlation matrix
    corr = ret_df.corr()
    print("Correlation matrix:")
    print(corr.round(3).to_string())

    # Ensemble methods
    n_strat = len(ret_df.columns)
    T = len(ret_df)

    # 1. Equal weight
    w_eq = np.ones(n_strat) / n_strat
    eq_ret = ret_df.values @ w_eq
    eq_sharpe = eq_ret.mean() / eq_ret.std() * np.sqrt(252) if eq_ret.std() > 0 else 0

    # 2. Inverse variance
    inv_var = 1.0 / ret_df.var().values
    w_iv = inv_var / inv_var.sum()
    iv_ret = ret_df.values @ w_iv
    iv_sharpe = iv_ret.mean() / iv_ret.std() * np.sqrt(252) if iv_ret.std() > 0 else 0

    # 3. Risk parity
    vols = ret_df.std().values
    w_rp = (1.0 / vols) / (1.0 / vols).sum()
    rp_ret = ret_df.values @ w_rp
    rp_sharpe = rp_ret.mean() / rp_ret.std() * np.sqrt(252) if rp_ret.std() > 0 else 0

    # 4. Mean-variance (with shrinkage)
    mu = ret_df.mean().values * 252
    cov = ret_df.cov().values * 252
    # Simple shrinkage to diagonal
    shrinkage = 0.3
    cov_shrunk = (1 - shrinkage) * cov + shrinkage * np.diag(np.diag(cov))
    try:
        inv_cov = np.linalg.inv(cov_shrunk)
        w_mv = inv_cov @ mu
        w_mv = w_mv / w_mv.sum()  # normalize
        mv_ret = ret_df.values @ w_mv
        mv_sharpe = mv_ret.mean() / mv_ret.std() * np.sqrt(252) if mv_ret.std() > 0 else 0
    except np.linalg.LinAlgError:
        w_mv = w_eq
        mv_ret = eq_ret
        mv_sharpe = eq_sharpe

    # 5. Min-variance
    try:
        w_minv = inv_cov @ np.ones(n_strat)
        w_minv = w_minv / w_minv.sum()
        minv_ret = ret_df.values @ w_minv
        minv_sharpe = minv_ret.mean() / minv_ret.std() * np.sqrt(252) if minv_ret.std() > 0 else 0
    except Exception:
        w_minv = w_eq
        minv_ret = eq_ret
        minv_sharpe = eq_sharpe

    # Print ensemble results
    portfolios = {
        "equal_weight": (w_eq, eq_sharpe, eq_ret),
        "inv_variance": (w_iv, iv_sharpe, iv_ret),
        "risk_parity": (w_rp, rp_sharpe, rp_ret),
        "mean_variance": (w_mv, mv_sharpe, mv_ret),
        "min_variance": (w_minv, minv_sharpe, minv_ret),
    }

    print(f"
{'Portfolio':<20} {'Sharpe':>8} {'AnnRet':>8} {'AnnVol':>8} {'MaxDD':>8}")
    print("-" * 60)
    for pname, (w, sh, rets) in portfolios.items():
        ann_ret = rets.mean() * 252
        ann_vol = rets.std() * np.sqrt(252)
        cum = (1 + rets).cumprod()
        max_dd = (cum / cum.cummax() - 1).min()
        print(f"{pname:<20} {sh:>8.3f} {ann_ret:>8.3f} {ann_vol:>8.3f} {max_dd:>8.3f}")
        print(f"  weights: {dict(zip(ret_df.columns, w.round(3)))}")

    # Save results
    ensemble_results = {
        "strategies": {k: {"sharpe": float(v["sharpe"]), "ann_ret": float(v["ann_ret"])}
                       for k, v in results.items() if "sharpe" in v},
        "correlation": corr.round(4).to_dict(),
        "portfolios": {},
    }
    for pname, (w, sh, rets) in portfolios.items():
        ensemble_results["portfolios"][pname] = {
            "sharpe": float(sh),
            "ann_ret": float(rets.mean() * 252),
            "ann_vol": float(rets.std() * np.sqrt(252)),
            "max_dd": float((1 + rets).cumprod().div((1 + rets).cumprod().cummax()).min()),
            "weights": {str(c): float(w[j]) for j, c in enumerate(ret_df.columns)},
        }
    with open(os.path.join(out_dir, "ensemble_results.json"), "w") as f:
        json.dump(ensemble_results, f, indent=2, default=str)

    # Save ensemble daily returns
    ens_ret_df = pd.DataFrame({pname: rets for pname, (w, sh, rets) in portfolios.items()},
                               index=ret_df.index)
    ens_ret_df.to_csv(os.path.join(out_dir, "ensemble_daily_returns.csv"))

print("
=== Ensemble build complete ===")
