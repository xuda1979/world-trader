"""Optimized sweep: relaxed ICIR screen + tree models."""
from __future__ import annotations
import os, sys, json, time, warnings
warnings.filterwarnings('ignore')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path: sys.path.insert(0, ROOT)

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
        # Relaxed ICIR: keep ~12-15 best factors
        icir_threshold=0.10, ic_mean_threshold=0.005,
        ic_bonferroni=False, ic_sign_check=True,
    )

def run_all():
    configs = []
    
    # 1. GBRT d=2, relaxed ICIR (~12 factors)
    c = base().copy(name="gbrt_d2_relax", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5)
    configs.append(c)
    
    # 2. RF d=5, 500 trees, relaxed ICIR
    c = base().copy(name="rf_d5_n500_relax", model_method="rf",
        rf_n_estimators=500, rf_max_depth=5,
        rf_min_samples_leaf=20, rf_max_features="sqrt",
        gbrt_pred_smooth=0.4)
    configs.append(c)
    
    # 3. RF d=8, 500 trees, relaxed ICIR
    c = base().copy(name="rf_d8_n500_relax", model_method="rf",
        rf_n_estimators=500, rf_max_depth=8,
        rf_min_samples_leaf=15, rf_max_features="sqrt",
        gbrt_pred_smooth=0.4)
    configs.append(c)
    
    # 4. GBRT d=3, more trees, relaxed ICIR
    c = base().copy(name="gbrt_d3_n300_relax", model_method="gbrt",
        gbrt_n_estimators=300, gbrt_max_depth=3,
        gbrt_learning_rate=0.03, gbrt_pred_smooth=0.5)
    configs.append(c)
    
    # 5. GBRT d=2, huber, relaxed ICIR
    c = base().copy(name="gbrt_d2_huber_relax", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        gbrt_loss="huber", gbrt_alpha=0.9)
    configs.append(c)
    
    # 6. GBRT d=2, exclude bottom 50% of factors
    c = base().copy(name="gbrt_d2_exclude", model_method="gbrt",
        gbrt_n_estimators=200, gbrt_max_depth=2,
        gbrt_learning_rate=0.05, gbrt_pred_smooth=0.5,
        factor_exclude=("downside_skew", "skew_60d", "reversal_1w",
                        "reversal_3w", "vol_surprise", "mom_1m",
                        "mom_12m_squared", "ohlc_gap_reversal",
                        "ohlc_overnight_intraday_ratio", "ohlc_gap_5d",
                        "ohlc_range_trend", "ohlc_ad_line"))
    configs.append(c)
    
    # 7. RF d=8, exclude bottom factors, bypass
    c = base().copy(name="rf_d8_exclude", model_method="rf",
        rf_n_estimators=500, rf_max_depth=8,
        rf_min_samples_leaf=15, rf_max_features="sqrt",
        gbrt_pred_smooth=0.4, bypass_ic_screen=True,
        factor_exclude=("downside_skew", "skew_60d", "reversal_1w",
                        "reversal_3w", "vol_surprise", "mom_1m",
                        "ohlc_gap_reversal", "ohlc_overnight_intraday_ratio",
                        "ohlc_gap_5d", "ohlc_range_trend", "ohlc_ad_line"))
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
                "time_s": round(time.time() - tn, 1),
                "n_factors": len(bundle["kept_factors"]),
            }
            results.append(row)
            print(f"  S={row['sharpe']:.3f} R={row['ann_ret']:.2%} DD={row['max_dd']:.2%} TO={row['turnover']:.1f} {row['verdict']}({row['n_flags']}f) [{row['n_factors']}f]")
        except Exception as e:
            import traceback; traceback.print_exc()
            results.append({"name": cfg.name, "error": str(e)[:200]})
    
    results.sort(key=lambda r: r.get("sharpe", -999), reverse=True)
    print(f"\nSWEEP COMPLETE")
    for r in results:
        if "error" in r:
            print(f"  {r['name']:<25s} ERROR: {r['error'][:60]}")
        else:
            print(f"  {r['name']:<25s} {r['model']:<12s} S={r['sharpe']:.3f} R={r['ann_ret']:.2%} DD={r['max_dd']:.2%} TO={r['turnover']:.1f} {r['verdict']}({r['n_flags']}f) [{r['n_factors']}f]")
    import pandas as pd
    pd.DataFrame(results).to_csv(os.path.join(ROOT, "tools/quant/ls/results/sweep_v3_results.csv"), index=False)
    return results

if __name__ == "__main__":
    run_all()
