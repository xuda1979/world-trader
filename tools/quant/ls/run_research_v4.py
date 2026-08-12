"""V4 Research Sweep: push Sharpe > 1.5 with realistic costs (3.8bps).

Key directions (config-only, no new code needed):
  1. Regularized GBRT: subsample < 1.0, more n_est, lower LR
  2. Relaxed ICIR pre-filter: keep top ~15 factors instead of 33
  3. RF with shallow trees: bagging reduces variance on small data
  4. Prediction smoothing + clipping sweep
  5. Concentrated portfolios (n=5, higher leverage)

Building on V3 baseline: GBRT d=2, Sharpe 1.237, bypass_ic_screen=True.
"""
from __future__ import annotations
import os, sys, time, warnings
warnings.filterwarnings("ignore")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


def _base(method="gbrt", bypass=True):
    """Baseline config matching V3 best (Sharpe 1.237)."""
    return Config(
        name="v4_base",
        predict_horizon=10, return_horizon_fwd=10,
        train_window=120, refit_freq=5, rebalance_freq=5,
        model_method=method, use_extra_factors=True, use_ohlc_factors=True,
        bypass_ic_screen=bypass,
        n_long=10, n_short=10, weighting="mean_var", opt_lambda_risk=0.5,
        position_cap_pct=0.20, gross_leverage=1.6, max_gross_leverage=2.0,
        use_call_rate_financing=True, long_financing_apply=True,
        cost_bps_one_side=3.8, cost_round_trip_bps=7.6, slippage_bps=1.0,
        diag_window_sweep=(100, 120, 140), plot=False, verbose=False,
        save_intermediate=False,
    )


def _gb1(name, **kw):
    """GBRT d=2 baseline."""
    c = _base("gbrt", bypass=True).copy(name=name)
    c.set(gbrt_n_estimators=200, gbrt_max_depth=2, gbrt_learning_rate=0.05,
          gbrt_min_samples_leaf=20, gbrt_max_features="sqrt",
          gbrt_label_transform="zscore", gbrt_label_residual="demean",
          gbrt_label_winsorize=0.01, gbrt_pred_smooth=0.5, gbrt_pred_clip=4.0)
    c.set(**kw)
    return c


def _rf1(name, **kw):
    """RF baseline."""
    c = _base("rf", bypass=True).copy(name=name)
    c.set(rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
          rf_max_features="sqrt", gbrt_pred_smooth=0.4, gbrt_pred_clip=4.0)
    c.set(**kw)
    return c


def build_configs():
    configs = []

    # row 0: V3 baseline reference
    configs.append(_gb1("v4_baseline_d2"))

    # SWEEP A: GBRT regularization
    for s in [0.5, 0.6, 0.7, 0.8]:
        configs.append(_gb1("v4_gb_sub%d" % int(s*100),
            gbrt_subsample=s, gbrt_n_estimators=300, gbrt_learning_rate=0.03))

    for leaf in [20, 30, 50]:
        configs.append(_gb1("v4_gb_leaf%d" % leaf, gbrt_min_samples_leaf=leaf))

    for d in [1, 3]:
        configs.append(_gb1("v4_gb_depth%d" % d, gbrt_max_depth=d))

    for n_est, lr in [(400, 0.02), (500, 0.015), (300, 0.03)]:
        configs.append(_gb1("v4_gb_n%d_lr%d" % (n_est, int(lr*1000)),
            gbrt_n_estimators=n_est, gbrt_learning_rate=lr))

    for a in [0.85, 0.90, 0.95]:
        configs.append(_gb1("v4_gb_huber_a%d" % int(a*100),
            gbrt_loss="huber", gbrt_alpha=a))

    # SWEEP B: Prediction smoothing + clip
    for sm in [0.3, 0.6, 0.7, 0.8]:
        configs.append(_gb1("v4_gb_sm%d" % int(sm*100), gbrt_pred_smooth=sm))

    for cl in [2.0, 3.0, 5.0, 6.0]:
        configs.append(_gb1("v4_gb_cl%d" % int(cl*10), gbrt_pred_clip=cl))

    # SWEEP C: RF
    for d in [2, 4, 5, 7]:
        configs.append(_rf1("v4_rf_d%d" % d, rf_max_depth=d, gbrt_pred_smooth=0.5))

    for n in [300, 800, 1000]:
        configs.append(_rf1("v4_rf_n%d" % n, rf_n_estimators=n, gbrt_pred_smooth=0.5))

    # SWEEP D: Relaxed ICIR pre-filter
    for t_ic, t_mean in [(0.03, 0.002), (0.05, 0.003), (0.08, 0.005), (0.10, 0.008)]:
        configs.append(_gb1("v4_gb_screen_%d" % int(t_ic*1000),
            bypass_ic_screen=False, icir_threshold=t_ic,
            ic_mean_threshold=t_mean, ic_bonferroni=False))

    # RF with relaxed screen
    c = _base("rf", bypass=False).copy(name="v4_rf_screen_50")
    c.set(icir_threshold=0.05, ic_mean_threshold=0.003, ic_bonferroni=False,
          rf_n_estimators=500, rf_max_depth=3, rf_min_samples_leaf=20,
          rf_max_features="sqrt", gbrt_pred_smooth=0.4, gbrt_pred_clip=4.0)
    configs.append(c)

    # SWEEP E: Concentration & leverage
    for n in [5, 8, 12, 15]:
        configs.append(_gb1("v4_gb_n%d" % n, n_long=n, n_short=n))
    for n, cap in [(5, 0.30), (6, 0.25), (8, 0.25)]:
        configs.append(_gb1("v4_gb_n%d_cap%d" % (n, int(cap*100)),
            n_long=n, n_short=n, position_cap_pct=cap))
    for lev in [1.2, 1.4, 2.0]:
        configs.append(_gb1("v4_gb_lev%d" % int(lev*10),
            gross_leverage=lev, max_gross_leverage=min(lev*1.5, 3.0)))

    # SWEEP F: Vol-scale label
    configs.append(_gb1("v4_gb_volscale",
        gbrt_label_vol_scale=True, gbrt_label_vol_window=60,
        gbrt_label_winsorize=0.02))

    # SWEEP G: Horizon sweep
    for h in [5, 15, 21]:
        configs.append(_gb1("v4_gb_h%d" % h,
            predict_horizon=h, return_horizon_fwd=h))

    # SWEEP H: Combined best
    configs.append(_gb1("v4_gb_stable1",
        gbrt_subsample=0.7, gbrt_min_samples_leaf=30,
        gbrt_n_estimators=300, gbrt_learning_rate=0.03,
        gbrt_max_depth=2, gbrt_pred_smooth=0.5))
    configs.append(_gb1("v4_gb_stable2",
        gbrt_subsample=0.7, gbrt_min_samples_leaf=40,
        gbrt_n_estimators=400, gbrt_learning_rate=0.02,
        gbrt_max_depth=2, gbrt_pred_smooth=0.6))
    configs.append(_gb1("v4_gb_screen_stable",
        bypass_ic_screen=False,
        icir_threshold=0.05, ic_mean_threshold=0.003, ic_bonferroni=False,
        gbrt_subsample=0.7, gbrt_min_samples_leaf=30,
        gbrt_n_estimators=300, gbrt_learning_rate=0.03,
        gbrt_max_depth=2, gbrt_pred_smooth=0.6))

    # SWEEP I: MV lambda
    for lam in [0.3, 1.0, 2.0, 3.0]:
        configs.append(_gb1("v4_gb_mvlam%d" % int(lam*10), opt_lambda_risk=lam))

    # SWEEP J: Weighting
    for w in ["risk_parity", "equal", "shrunk"]:
        configs.append(_gb1("v4_gb_wt_%s" % w, weighting=w))

    return configs


def main():
    configs = build_configs()
    print("Running %d V4 research configs..." % len(configs))
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
            print("  S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s(%df) [%df]" % (
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
    print("V4 SWEEP COMPLETE (%d configs, %.1f min)" % (len(configs), elapsed))
    print("="*70)

    for rank, r in enumerate(results[:20]):
        if "error" in r:
            print("  %d. %s ERROR: %s" % (rank+1, r["name"], r["error"][:60]))
        else:
            print("  %d. %-30s S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s(%df)" % (
                rank+1, r["name"], r["sharpe"], r["ann_ret"]*100,
                r["max_dd"]*100, r["turnover"], r["verdict"], r["n_flags"]))

    print("\nTOP 10 CONFIGS")
    print("-"*70)
    for rank, r in enumerate(results[:10]):
        if "error" in r:
            continue
        print("\n--- %d. %s ---" % (rank+1, r["name"]))
        print("  Sharpe=%.3f  AnnRet=%.2f%%  AnnVol=%.2f%%  MaxDD=%.2f%%" % (
            r["sharpe"], r["ann_ret"]*100, r["ann_vol"]*100, r["max_dd"]*100))
        print("  Sortino=%.3f  Turnover=%.1f  Model=%s  Verdict=%s  Flags=%d: %s  N_factors=%d" % (
            r["sortino"], r["turnover"], r["model"], r["verdict"],
            r["n_flags"], r.get("flags",""), r["n_factors"]))

    import pandas as pd
    out_path = os.path.join(ROOT, "tools/quant/ls/results/v4_sweep_results.csv")
    pd.DataFrame(results).to_csv(out_path, index=False)
    print("\nResults saved to %s" % out_path)
    return results


if __name__ == "__main__":
    main()
