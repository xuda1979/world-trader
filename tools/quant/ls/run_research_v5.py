"""V5 Research: push Sharpe higher using correct baseline (1.237 config).

Key findings from config audit:
  - Original 1.237 used: base 14 factors only, vol_target_active=True (30%),
    n_long=13, rebalance_freq=10, gross_leverage=1.0
  - V4 sweep used wrong config (extra/OHLC factors, no vol target)
  - Key amplifier: vol_target_active scales returns during low-vol periods

This script tests improvements on the CORRECT baseline:
  1. Ensemble (GBRT + RF) — model averaging
  2. Relaxed ICIR pre-filter — keep ~14 factors, drop noise
  3. Subsampled GBRT — stochastic GB for regularization
  4. RF-only — bagging may generalize better
  5. Multi-horizon — blend h=5,10 predictions
"""
from __future__ import annotations
import os, sys, time, warnings
warnings.filterwarnings("ignore")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


def _base_correct(name, method="gbrt", bypass=False):
    """UPDATED baseline matching gbrt_best_repro (Sharpe 1.683).

    Key differences from s05_d2 (1.237):
      - Relaxed ICIR screen (threshold=0.10) keeps ~11 factors
      - use_extra_factors=True (rank_mom, resid_mom, etc.)
      - gross_leverage=1.6 (instead of 1.0)
      - n_long=10 (instead of 13)
      - No vol target (vol_target_active=False)
    """
    return Config(
        name=name,
        predict_horizon=10, return_horizon_fwd=10,
        train_window=120, refit_freq=5, rebalance_freq=5,
        model_method=method,
        use_extra_factors=True,     # KEY: extra factors help GBRT
        use_ohlc_factors=False,     # KEY: no OHLC (noise)
        bypass_ic_screen=bypass,
        icir_threshold=0.10, ic_mean_threshold=0.005, ic_bonferroni=False,
        n_long=10, n_short=10,
        weighting="mean_var", opt_lambda_risk=0.5,
        position_cap_pct=0.20,
        gross_leverage=1.6, max_gross_leverage=2.0,
        vol_target_active=False,
        beta_max_abs=0.25,
        use_call_rate_financing=True, long_financing_apply=True,
        cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
        diag_window_sweep=(100, 120, 140), plot=False, verbose=False,
        save_intermediate=False, out_dir="tools/quant/ls/results",
        seed=42,
    )


def _gbrt(name, **kw):
    c = _base_correct(name, "gbrt", bypass=False)
    c.set(
        gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    )
    c.set(**kw)
    return c


def build_configs():
    configs = []

    # 0. Baseline: exact match of gbrt_best_repro (Sharpe 1.683 expected)
    configs.append(_gbrt("v5_baseline"))

    # 1. Ensemble GBRT+RF with relaxed screen
    configs.append(_base_correct("v5_ensemble", "ensemble", bypass=False).set(
        gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 2. Ensemble with bypass (all 21 factors)
    configs.append(_base_correct("v5_ensemble_bypass", "ensemble", bypass=True).set(
        gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 3. Ensemble with RF depth=2 (shallower = less overfit)
    configs.append(_base_correct("v5_ensemble_rfd2", "ensemble", bypass=False).set(
        gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        rf_n_estimators=500, rf_max_depth=2, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 4. RF-only with relaxed screen
    configs.append(_base_correct("v5_rf_d3", "rf", bypass=False).set(
        rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))
    configs.append(_base_correct("v5_rf_d2", "rf", bypass=False).set(
        rf_n_estimators=800, rf_max_depth=2, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 5. GBRT subsample (stochastic GBRT for regularization)
    for s in [0.6, 0.7, 0.8]:
        configs.append(_gbrt("v5_gb_sub%d" % int(s*100),
            gbrt_subsample=s, gbrt_n_estimators=300, gbrt_learning_rate=0.03))

    # 6. GBRT huber loss (robust to fat tails)
    for a in [0.85, 0.90, 0.95]:
        configs.append(_gbrt("v5_gb_huber_a%d" % int(a*100),
            gbrt_loss="huber", gbrt_alpha=a))

    # 7. Ensemble + subsample
    configs.append(_base_correct("v5_ensemble_sub7", "ensemble", bypass=False).set(
        gbrt_n_estimators=300, gbrt_max_depth=2, gbrt_learning_rate=0.03,
        gbrt_subsample=0.7, gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 8. Ensemble + huber
    configs.append(_base_correct("v5_ensemble_huber", "ensemble", bypass=False).set(
        gbrt_loss="huber", gbrt_alpha=0.9,
        gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
        gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
        rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
        rf_max_features="sqrt",
        gbrt_label_transform="zscore", gbrt_label_residual="demean",
        gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0,
    ))

    # 9. Higher leverage tests
    for lev in [1.8, 2.0]:
        configs.append(_gbrt("v5_gb_lev%d" % int(lev*10),
            gross_leverage=lev, max_gross_leverage=min(lev*1.5, 3.0)))

    # 10. More names (breadth boost)
    for n in [13, 15]:
        configs.append(_gbrt("v5_gb_n%d" % n, n_long=n, n_short=n))

    return configs


def main():
    configs = build_configs()
    print("Running %d V5 research configs (correct baseline)..." % len(configs))
    results = []
    t0 = time.time()

    for i, cfg in enumerate(configs):
        tn = time.time()
        print("\n[%d/%d] %s..." % (i+1, len(configs), cfg.name))
        try:
            bundle = runner.run(cfg, export=True)
            m = bundle["metrics"]
            v = bundle["diagnostics"]["verdict"]
            row = {
                "name": cfg.name, "model": cfg.model_method,
                "sharpe": round(m.get("sharpe", 0), 4),
                "ann_ret": round(m.get("annual_return", 0), 4),
                "ann_vol": round(m.get("annual_volatility", 0), 4),
                "max_dd": round(m.get("max_drawdown", 0), 4),
                "sortino": round(m.get("sortino", 0), 4),
                "turnover": round(m.get("annual_turnover", 0), 2),
                "verdict": v.get("assessment", "?"),
                "n_flags": v.get("n_flags", -1),
                "flags": "; ".join(v.get("overfitting_flags", [])),
                "time_s": round(time.time() - tn, 1),
                "n_factors": len(bundle.get("kept_factors", [])),
            }
            results.append(row)
            print("  S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s(%d flags) [%d factors]" % (
                row["sharpe"], row["ann_ret"]*100, row["max_dd"]*100,
                row["turnover"], row["verdict"], row["n_flags"],
                row["n_factors"]))
        except Exception as e:
            import traceback
            traceback.print_exc()
            results.append({"name": cfg.name, "error": str(e)[:200]})
            print("  ERROR: %s" % e)

    elapsed = (time.time() - t0) / 60.0
    results.sort(key=lambda r: r.get("sharpe", -999), reverse=True)

    print("\n" + "="*70)
    print("V5 SWEEP COMPLETE (%d configs, %.1f min)" % (len(configs), elapsed))
    print("="*70)

    for rank, r in enumerate(results):
        if "error" in r:
            print("  %d. %-30s ERROR: %s" % (rank+1, r["name"], r["error"][:60]))
        else:
            print("  %d. %-30s S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s(%d)" % (
                rank+1, r["name"], r["sharpe"], r["ann_ret"]*100,
                r["max_dd"]*100, r["turnover"], r["verdict"], r["n_flags"]))

    print("\nTOP CONFIGS:")
    for rank, r in enumerate(results[:10]):
        if "error" in r: continue
        print("  %d. %-30s S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s [%d factors]" % (
            rank+1, r["name"], r["sharpe"], r["ann_ret"]*100,
            r["max_dd"]*100, r["turnover"], r["verdict"], r["n_factors"]))

    import pandas as pd
    out_path = os.path.join(ROOT, "tools/quant/ls/results/v5_sweep_results.csv")
    pd.DataFrame(results).to_csv(out_path, index=False)
    print("\nResults saved to %s" % out_path)
    return results


if __name__ == "__main__":
    main()
