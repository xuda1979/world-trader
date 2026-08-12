"""Targeted research sweep: test the most promising configs."""
from __future__ import annotations
import os, sys, json, time, warnings
warnings.filterwarnings('ignore')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .config import Config
from . import runner

def base():
    return Config(
        predict_horizon=10, return_horizon_fwd=10,
        train_window=120, refit_freq=5, rebalance_freq=5,
        use_ohlc_factors=True, use_extra_factors=True,
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01,
        n_long=10, n_short=10, weighting="mean_var",
        opt_lambda_risk=0.5, position_cap_pct=0.20,
        gross_leverage=1.6, max_gross_leverage=2.0,
        use_call_rate_financing=True, long_financing_apply=True,
        cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
        diag_window_sweep=(100, 120, 140), plot=False, verbose=False,
    )

def run_all():
    configs = []
    
    # 1. GBRT d=2 baseline with ICIR screen
    c = base().copy(name="gbrt_d2_icir", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        bypass_ic_screen=False)
    configs.append(c)
    
    # 2. GBRT d=2, bypass screen (all 33 factors)
    c = base().copy(name="gbrt_d2_bypass", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        bypass_ic_screen=True)
    configs.append(c)
    
    # 3. GBRT d=3, more trees, ICIR screen
    c = base().copy(name="gbrt_d3_n300", model_method="gbrt",
        gbrt_n_estimators=300, gbrt_max_depth=3,
        gbrt_learning_rate=0.03, gbrt_pred_smooth=0.5,
        bypass_ic_screen=False)
    configs.append(c)
    
    # 4. GBRT d=2, huber loss
    c = base().copy(name="gbrt_d2_huber", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        gbrt_loss="huber", gbrt_alpha=0.9,
        bypass_ic_screen=False)
    configs.append(c)
    
    # 5. GBRT d=2, vol-scaled label
    c = base().copy(name="gbrt_d2_volscale", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        gbrt_label_vol_scale=True, gbrt_label_vol_window=60,
        bypass_ic_screen=False)
    configs.append(c)
    
    # 6. RF depth=5, 500 trees, ICIR screen
    c = base().copy(name="rf_d5_n500", model_method="rf",
        rf_n_estimators=500, rf_max_depth=5,
        rf_min_samples_leaf=20, rf_max_features="sqrt",
        gbrt_pred_smooth=0.4, bypass_ic_screen=False)
    configs.append(c)
    
    # 7. RF depth=8, 500 trees, bypass screen
    c = base().copy(name="rf_d8_n500_bypass", model_method="rf",
        rf_n_estimators=500, rf_max_depth=8,
        rf_min_samples_leaf=15, rf_max_features="sqrt",
        gbrt_pred_smooth=0.4, bypass_ic_screen=True)
    configs.append(c)
    
    # 8. ElasticNet with ICIR screen
    c = base().copy(name="enet_cv5", model_method="elasticnet",
        enet_cv_folds=5, model_weight_smooth=0.3,
        bypass_ic_screen=False)
    configs.append(c)
    
    # 9. GBRT d=2, exclude decayed factors
    c = base().copy(name="gbrt_d2_nodkv", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        bypass_ic_screen=False,
        factor_exclude=("vol_60d", "skew_60d", "downside_skew", "range_vol_60d"))
    configs.append(c)
    
    # 10. GBRT h=5 (faster signal rotation)
    c = base().copy(name="gbrt_h5_d2", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.4,
        predict_horizon=5, return_horizon_fwd=5,
        bypass_ic_screen=False)
    configs.append(c)
    
    results = []
    t0 = time.time()
    for i, cfg in enumerate(configs):
        tn = time.time()
        print(f"\n[{i+1}/{len(configs)}] {cfg.name}...")
        try:
            bundle = runner.run(cfg, export=True)
            m = bundle['metrics']; v = bundle['diagnostics']['verdict']
            row = {
                "name": cfg.name, "model": cfg.model_method,
                "sharpe": m.get("sharpe", float("nan")),
                "ann_ret": m.get("annual_return", float("nan")),
                "ann_vol": m.get("annual_volatility", float("nan")),
                "max_dd": m.get("max_drawdown", float("nan")),
                "sortino": m.get("sortino", float("nan")),
                "turnover": m.get("annual_turnover", float("nan")),
                "verdict": v.get("assessment", "?"),
                "n_flags": v.get("n_flags", -1),
                "flags": "; ".join(v.get("overfitting_flags", [])),
                "time_s": round(time.time() - tn, 1),
                "n_factors": len(bundle["kept_factors"]),
            }
            results.append(row)
            print(f"  S={row['sharpe']:.3f} R={row['ann_ret']:.2%} DD={row['max_dd']:.2%} TO={row['turnover']:.1f} {row['verdict']}({row['n_flags']}f) [{row['n_factors']}f]")
        except Exception as e:
            import traceback; traceback.print_exc()
            results.append({"name": cfg.name, "error": str(e)[:200]})
            print(f"  ERROR: {e}")
    
    results.sort(key=lambda r: r.get("sharpe", -999), reverse=True)
    print(f"\nSWEEP COMPLETE ({len(configs)} configs, {time.time()-t0:.0f}s)")
    for r in results:
        if "error" in r:
            print(f"  {r['name']:<25s} ERROR: {r['error'][:60]}")
        else:
            print(f"  {r['name']:<25s} {r['model']:<12s} S={r['sharpe']:.3f} R={r['ann_ret']:.2%} DD={r['max_dd']:.2%} TO={r['turnover']:.1f} {r['verdict']}({r['n_flags']}f) [{r['n_factors']}f]")
    
    import pandas as pd
    out_dir = os.path.join(ROOT, "tools/quant/ls/results")
    pd.DataFrame(results).to_csv(os.path.join(out_dir, "sweep_v2_results.csv"), index=False)
    return results

if __name__ == "__main__":
    run_all()
