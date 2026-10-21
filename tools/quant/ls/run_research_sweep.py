"""Comprehensive research sweep: test all new models + configs.
Run with: python -m tools.quant.ls.run_research_sweep
"""
from __future__ import annotations
import os, sys, json, time
from typing import Dict, List, Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .config import Config
from . import runner


def base_config() -> Config:
    """Best known base: GBRT h=10, d=2, demean+zscore, financing-on."""
    return Config().copy(**{
        "name": "research_base",
        "predict_horizon": 10,
        "return_horizon_fwd": 10,
        "train_window": 120,
        "refit_freq": 5,
        "rebalance_freq": 5,
        "model_method": "gbrt",
        # GBRT settings
        "gbrt_n_estimators": 200,
        "gbrt_max_depth": 2,
        "gbrt_learning_rate": 0.05,
        "gbrt_subsample": 1.0,
        "gbrt_min_samples_leaf": 20,
        "gbrt_max_features": "sqrt",
        "gbrt_loss": "squared_error",
        "gbrt_pred_clip": 4.0,
        "gbrt_pred_smooth": 0.5,
        "gbrt_label_transform": "zscore",
        "gbrt_label_residual": "demean",
        "gbrt_label_winsorize": 0.01,
        # Bypass IC screen - let tree models do feature selection
        "bypass_ic_screen": True,
        "use_extra_factors": True,
        # Portfolio
        "n_long": 10, "n_short": 10,
        "weighting": "mean_var",
        "opt_lambda_risk": 0.5,
        "position_cap_pct": 0.20,
        "gross_leverage": 1.6,
        "max_gross_leverage": 2.0,
        # Financing
        "use_call_rate_financing": True,
        "short_rebate_paid_bps": 150.0,
        "short_borrow_fee_etb_bps": 25.0,
        "long_financing_apply": True,
        # Costs
        "cost_bps_one_side": 3.8,
        "cost_round_trip_bps": 7.6,
        "slippage_bps": 1.0,
        # Diagnostics
        "diag_window_sweep": (100, 120, 140),
        "diag_weight_vol_flag": True,
        "diag_regime_split": True,
        # Output
        "out_dir": "tools/quant/ls/results",
    })


def make_sweep_configs() -> List[Config]:
    """Generate all configs for the research sweep."""
    base = base_config()
    configs = []

    # ---- 1. GBRT variants (vol_scale, huber loss, sign label) ----
    for label in ["gbrt_vol_scale", "gbrt_huber", "gbrt_sign"]:
        c = base.copy(name=label)
        if label == "gbrt_vol_scale":
            c.set(gbrt_label_vol_scale=True, gbrt_label_vol_window=60)
        elif label == "gbrt_huber":
            c.set(gbrt_loss="huber", gbrt_alpha=0.9)
        elif label == "gbrt_sign":
            c.set(gbrt_label_transform="sign")
        configs.append(c)

    # ---- 2. GBRT deeper trees with more regularization ----
    for depth in [3, 4]:
        for n_est in [150, 300]:
            c = base.copy(name=f"gbrt_d{depth}_n{n_est}")
            c.set(gbrt_max_depth=depth, gbrt_n_estimators=n_est)
            configs.append(c)

    # ---- 3. RandomForest variants ----
    for depth in [3, 5, 8]:
        for n_est in [300, 500]:
            for smooth in [0.3, 0.5]:
                c = base.copy(name=f"rf_d{depth}_n{n_est}_s{smooth}")
                c.set(
                    model_method="rf",
                    rf_n_estimators=n_est,
                    rf_max_depth=depth,
                    rf_min_samples_leaf=20,
                    rf_max_features="sqrt",
                    gbrt_pred_smooth=smooth,
                )
                configs.append(c)

    # ---- 4. ElasticNet variants ----
    for cv_folds in [3, 5]:
        c = base.copy(name=f"enet_cv{cv_folds}")
        c.set(
            model_method="elasticnet",
            enet_cv_folds=cv_folds,
            model_weight_smooth=0.3,
            bypass_ic_screen=False,  # let ICIR screen filter first
        )
        configs.append(c)

    # ---- 5. GBRT with different horizons ----
    for h in [5, 21]:
        c = base.copy(name=f"gbrt_h{h}")
        c.set(predict_horizon=h, return_horizon_fwd=h)
        configs.append(c)

    # ---- 6. Combined: GBRT d=2 + vol_scale + huber ----
    c = base.copy(name="gbrt_d2_vol_huber")
    c.set(gbrt_label_vol_scale=True, gbrt_loss="huber", gbrt_alpha=0.9)
    configs.append(c)

    # ---- 7. RF d=5 + different horizons ----
    for h in [5, 10]:
        c = base.copy(name=f"rf_d5_h{h}")
        c.set(
            model_method="rf",
            rf_n_estimators=500,
            rf_max_depth=5,
            rf_min_samples_leaf=15,
            rf_max_features="sqrt",
            gbrt_pred_smooth=0.4,
            predict_horizon=h,
            return_horizon_fwd=h,
        )
        configs.append(c)

    # ---- 8. High-leverage concentrated GBRT ----
    c = base.copy(name="gbrt_d2_conc")
    c.set(
        n_long=6, n_short=6,
        gross_leverage=2.0,
        max_gross_leverage=2.5,
        position_cap_pct=0.30,
        gbrt_max_depth=2,
        gbrt_n_estimators=250,
        gbrt_pred_smooth=0.4,
    )
    configs.append(c)

    return configs


def run_sweep():
    """Run all configs and report results."""
    configs = make_sweep_configs()
    print(f"Running {len(configs)} configs...")
    results = []
    t0 = time.time()

    for i, cfg in enumerate(configs):
        tn = time.time()
        print(f"\n[{i+1}/{len(configs)}] {cfg.name}...")
        try:
            bundle = runner.run(cfg, export=True)
            m = bundle["metrics"]
            v = bundle["diagnostics"]["verdict"]
            row = {
                "name": cfg.name,
                "model": cfg.model_method,
                "sharpe": m.get("sharpe", float("nan")),
                "ann_ret": m.get("annual_return", float("nan")),
                "ann_vol": m.get("annual_volatility", float("nan")),
                "max_dd": m.get("max_drawdown", float("nan")),
                "sortino": m.get("sortino", float("nan")),
                "calmar": m.get("calmar", float("nan")),
                "turnover": m.get("annual_turnover", float("nan")),
                "verdict": v.get("assessment", "?"),
                "n_flags": v.get("n_flags", -1),
                "flags": "; ".join(v.get("overfitting_flags", [])),
                "time_s": round(time.time() - tn, 1),
            }
            results.append(row)
            print(f"  Sharpe={row['sharpe']:.3f} ret={row['ann_ret']:.2%} "
                  f"dd={row['max_dd']:.2%} to={row['turnover']:.1f} "
                  f"{row['verdict']}({row['n_flags']}f)")
        except Exception as e:
            results.append({"name": cfg.name, "error": str(e)[:200]})
            print(f"  ERROR: {e}")

    # Sort by Sharpe
    results.sort(key=lambda r: r.get("sharpe", -999), reverse=True)
    print(f"\n{'='*100}")
    print(f"SWEEP COMPLETE ({len(configs)} configs, {time.time()-t0:.0f}s)")
    print(f"{'='*100}")
    print(f"{'Name':<30s} {'Model':<12s} {'Sharpe':>8s} {'AnnRet':>8s} "
          f"{'MaxDD':>8s} {'Turn':>7s} {'Verdict':<16s} {'Flags':>5s}")
    print("-" * 100)
    for r in results:
        if "error" in r:
            print(f"{r['name']:<30s} ERROR: {r['error'][:50]}")
        else:
            print(f"{r['name']:<30s} {r['model']:<12s} {r['sharpe']:8.3f} "
                  f"{r['ann_ret']:8.2%} {r['max_dd']:8.2%} {r['turnover']:7.1f} "
                  f"{r['verdict']:<16s} {r['n_flags']:>5d}")

    # Save sweep CSV
    import pandas as pd
    out_dir = os.path.join(ROOT, "tools/quant/ls/results")
    pd.DataFrame(results).to_csv(os.path.join(out_dir, "research_sweep_v2.csv"), index=False)
    print(f"\nSaved to research_sweep_v2.csv")
    return results


if __name__ == "__main__":
    run_sweep()
