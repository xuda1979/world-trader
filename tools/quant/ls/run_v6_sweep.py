"""V6 Sweep: extend from verified baseline (S=1.237)."""
import sys, os, time
sys.path.insert(0, "/Users/daxu/software/world-trader")
from tools.quant.ls import runner
from tools.quant.ls.config import Config
import numpy as np

BASE = dict(
    model_method="gbrt", predict_horizon=10, return_horizon_fwd=10,
    train_window=120, refit_freq=5, rebalance_freq=5,
    gbrt_max_depth=2, gbrt_n_estimators=200, gbrt_learning_rate=0.05,
    gbrt_min_samples_leaf=20, gbrt_max_features="sqrt", gbrt_subsample=1.0,
    gbrt_pred_clip=4.0, gbrt_pred_smooth=0.5,
    gbrt_label_transform="zscore", gbrt_label_residual="demean",
    gbrt_label_winsorize=0.01, gbrt_loss="squared_error",
    bypass_ic_screen=None, icir_threshold=0.08, ic_mean_threshold=0.02,
    ic_bonferroni=True,
    use_extra_factors=False, use_ohlc_factors=False,
    n_long=10, n_short=10, weighting="mean_var", opt_lambda_risk=0.5,
    position_cap_pct=0.20, gross_leverage=1.6, max_gross_leverage=2.0,
    long_short_balance=True, beta_max_abs=0.05,
    use_call_rate_financing=True, short_borrow_apply=True,
    long_financing_apply=True, short_rebate_paid_bps=150.0,
    short_borrow_fee_etb_bps=25.0, long_financing_spread_bps=50.0,
    cost_bps_one_side=3.8, slippage_bps=1.0, t_plus_1=True,
    diag_window_sweep=(100,120,140),
    save_intermediate=False, plot=False, verbose=False,
)

configs = [
    ("v6_baseline", {}),
    ("v6_d3", dict(gbrt_max_depth=3)),
    ("v6_d3_n500", dict(gbrt_max_depth=3, gbrt_n_estimators=500)),
    ("v6_d3_n13", dict(gbrt_max_depth=3, n_long=13, n_short=13, gross_leverage=1.0)),
    ("v6_n500", dict(gbrt_n_estimators=500)),
    ("v6_n1000", dict(gbrt_n_estimators=1000, gbrt_learning_rate=0.03)),
    ("v6_d3_extraf", dict(gbrt_max_depth=3, use_extra_factors=True, use_ohlc_factors=True, bypass_ic_screen=None, icir_threshold=0.0, ic_bonferroni=False)),
    ("v6_d2_extraf", dict(use_extra_factors=True, use_ohlc_factors=True, bypass_ic_screen=None, icir_threshold=0.0, ic_bonferroni=False)),
]

print("Running %d configs..." % len(configs))
results = []
for name, overrides in configs:
    cfg_dict = dict(BASE, name=name)
    cfg_dict.update(overrides)
    cfg_dict["out_dir"] = "tools/quant/ls/results/v6_sweep/" + name
    cfg = Config.from_dict(cfg_dict)
    print("=== %s ===" % name)
    t0 = time.time()
    try:
        b = runner.run(cfg, export=True)
        dt = time.time() - t0
        m = b["metrics"]; v = b["diagnostics"]["verdict"]
        print("  S=%.3f R=%.2f%% DD=%.2f%% TO=%.1f %s(%df) dt=%ds" % (m.get("sharpe",0), m.get("annual_return",0)*100, m.get("max_drawdown",0)*100, m.get("annual_turnover",0), v["assessment"], v["n_flags"], int(dt)))
        results.append(dict(name=name, sharpe=m.get("sharpe",0), ann_ret=m.get("annual_return",0), ann_vol=m.get("annual_volatility",0), max_dd=m.get("max_drawdown",0), turnover=m.get("annual_turnover",0), sortino=m.get("sortino",0), calmar=m.get("calmar",0), verdict=v["assessment"], n_flags=v["n_flags"]))
    except Exception as e:
        import traceback; traceback.print_exc()
        results.append(dict(name=name, error=str(e)[:200]))

print("=== SUMMARY ===")
ok = sorted([r for r in results if r.get("sharpe",0) > 0.01], key=lambda r: r["sharpe"], reverse=True)
for i,r in enumerate(ok):
    print("%d. %-25s S=%.3f  ret=%.2f%%  dd=%.2f%%  TO=%.1f  %s(%df)" % (i+1, r["name"], r["sharpe"], r["ann_ret"]*100, r["max_dd"]*100, r["turnover"], r["verdict"], r["n_flags"]))
import pandas as pd
pd.DataFrame(results).to_csv("tools/quant/ls/results/v6_sweep_summary.csv", index=False)