"""Focused high-Sharpe sweep: all-factors GBRT + loss + vol-scale + depth.

Tests the most promising configurations targeting Sharpe > 1.5.

Sweep axes:
  - factors:      {4-factors (ICIR-screened), 23-factors (all)}
  - depth:        {1, 2, 3}
  - n_estimators: {500, 1000, 2000}
  - loss:         {squared_error, huber}
  - vol_scale:    {False, True}
  - pred_smooth:  {0.3, 0.5, 0.7}

Focus grid (~72 configs; ~2h on a fast machine):
  1. 23-factors × depth={1,2} × n_est={500,1000,2000} × loss={squared,huber} × vol_scale={F,T}
  2. Plus 4-factor baseline depth=2 × n_est=500 × vol_scale={F,T} for comparison
"""
from __future__ import annotations
import os, sys, time, itertools

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls import runner
from tools.quant.ls.config import Config
import pandas as pd

# Best 4-factor baseline (from gbrt_tune/s05_d2: Sharpe 1.237)
BASE4 = {
    "model_method": "gbrt",
    "bypass_ic_screen": False,
    "icir_threshold": 0.10, "ic_mean_threshold": 0.005,
    "ic_bonferroni": False, "ic_sign_check": True,
    "gbrt_max_depth": 2,
    "gbrt_n_estimators": 500,
    "gbrt_learning_rate": 0.05,
    "gbrt_min_samples_leaf": 20,
    "gbrt_max_features": "sqrt",
    "gbrt_subsample": 1.0,
    "gbrt_pred_clip": 4.0,
    "gbrt_pred_smooth": 0.5,
    "gbrt_label_transform": "zscore",
    "gbrt_label_residual": "demean",
    "gbrt_label_winsorize": 0.02,
    "gbrt_label_vol_scale": False,
    "gbrt_loss": "squared_error",
    "use_extra_factors": True,
    "n_long": 10, "n_short": 10, "use_fixed_n": True,
    "weighting": "mean_var", "opt_lambda_risk": 0.5,
    "position_cap_pct": 0.20, "gross_leverage": 1.6,
    "max_gross_leverage": 1.6, "vol_target_active": False,
    "long_short_balance": True, "beta_target": 0.0, "beta_max_abs": 0.05,
    "train_window": 120, "refit_freq": 5, "rebalance_freq": 5,
    "predict_horizon": 10, "return_horizon_fwd": 10,
    "t_plus_1": True, "cost_bps_one_side": 3.8, "slippage_bps": 1.0,
    "use_call_rate_financing": True, "short_borrow_apply": True,
    "long_financing_apply": True,
    "short_rebate_paid_bps": 150.0, "short_borrow_fee_etb_bps": 25.0,
    "long_financing_spread_bps": 50.0,
    "save_intermediate": False, "plot": False, "verbose": False,
}

# All-factors variant (bypass screen)
BASE23 = dict(BASE4, bypass_ic_screen=True)

def run_cfg(name, **overrides):
    """Run one config and return metrics dict."""
    cfg_dict = dict(overrides.pop("_base", BASE23), name=name, **overrides)
    cfg_dict["out_dir"] = "tools/quant/ls/results/hs_sweep/" + name
    cfg = Config.from_dict(cfg_dict)
    t0 = time.time()
    try:
        bundle = runner.run(cfg, export=True)
        dt = time.time() - t0
        m = bundle["metrics"]
        v = bundle["diagnostics"]["verdict"]
        params = {
            "config": name,
            "sharpe": m.get("sharpe", 0),
            "ann_ret": m.get("annual_return", 0),
            "ann_vol": m.get("annual_volatility", 0),
            "turnover": m.get("annual_turnover", 0),
            "max_dd": m.get("max_drawdown", 0),
            "sortino": m.get("sortino_ratio", 0),
            "calmar": m.get("calmar_ratio", 0),
            "verdict": v["assessment"],
            "n_flags": v["n_flags"],
            "n_kept": len(bundle["kept_factors"]),
            "runtime_s": dt,
            "final_eq": m.get("final_equity", 0),
        }
        # Record hyperparams for analysis
        for k in ["gbrt_max_depth", "gbrt_n_estimators", "gbrt_learning_rate",
                   "gbrt_pred_smooth", "gbrt_loss", "gbrt_label_vol_scale",
                   "gbrt_label_transform", "gbrt_label_residual"]:
            params[k] = overrides.get(k, BASE23.get(k, None))
        return params
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"config": name, "error": str(e), "runtime_s": time.time() - t0}

def main():
    grid = []

    # === Group 1: 23-factor core sweep ===
    depths = [1, 2, 3]
    n_ests_core = [500, 1000, 2000]
    losses = ["squared_error", "huber"]
    for d, n, loss in itertools.product(depths, n_ests_core, losses):
        grid.append(("all_d%d_n%d_%s" % (d, n, loss[:4]),
                     {"_base": BASE23, "gbrt_max_depth": d,
                      "gbrt_n_estimators": n, "gbrt_loss": loss}))
        # Also test vol-scaled variant
        grid.append(("all_d%d_n%d_%s_vs" % (d, n, loss[:4]),
                     {"_base": BASE23, "gbrt_max_depth": d,
                      "gbrt_n_estimators": n, "gbrt_loss": loss,
                      "gbrt_label_vol_scale": True,
                      "gbrt_label_winsorize": 0.03}))

    # === Group 2: 4-factor vol-scale test (baseline enhancement) ===
    for vol_scale in [False, True]:
        tag = "vs" if vol_scale else "base"
        grid.append(("f4_d2_n500_lr005_%s" % tag,
                     {"_base": BASE4, "gbrt_label_vol_scale": vol_scale,
                      "gbrt_label_winsorize": 0.03 if vol_scale else 0.02}))

    # === Group 3: Depth=1 stumps with extra high n_est ===
    for n in [3000, 5000]:
        for loss in ["squared_error", "huber"]:
            grid.append(("all_d1_n%d_%s" % (n, loss[:4]),
                         {"_base": BASE23, "gbrt_max_depth": 1,
                          "gbrt_n_estimators": n, "gbrt_loss": loss,
                          "gbrt_learning_rate": 0.01}))

    # === Group 4: Smooth sweep on best-looking configs ===
    # Run a focused smooth sweep on the all-factors depth=2 n=1000 config
    for smooth in [0.3, 0.5, 0.7, 0.85]:
        grid.append(("all_d2_n1000_s%.0f" % (smooth*100),
                     {"_base": BASE23, "gbrt_max_depth": 2,
                      "gbrt_n_estimators": 1000,
                      "gbrt_pred_smooth": smooth}))

    # === Group 5: Best 4-factor with more trees ===
    for n in [1000, 2000]:
        grid.append(("f4_d2_n%d" % n,
                     {"_base": BASE4, "gbrt_n_estimators": n}))

    print("=== HIGH-SHARPE FOCUSED SWEEP: %d configs ===" % len(grid))

    results = []
    t0_total = time.time()
    for i, (name, overrides) in enumerate(grid):
        print("\n[%d/%d] %s" % (i+1, len(grid), name))
        sys.stdout.flush()
        r = run_cfg(name, **overrides)
        results.append(r)
        if "sharpe" in r:
            print("  Sharpe=%.4f  AnnRet=%.4f  Vol=%.4f  TO=%.1f  DD=%.3f  %s(%d)  nf=%d  dt=%ds" % (
                r["sharpe"], r["ann_ret"], r["ann_vol"], r["turnover"],
                r["max_dd"], r["verdict"], r["n_flags"],
                r["n_kept"], int(r["runtime_s"])))
        else:
            print("  ERROR: %s" % r.get("error", "?"))

    # Summary
    df = pd.DataFrame(results)
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/hs_sweep")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "_summary.csv"), index=False)

    print("\n=== DONE in %.1f min ===" % ((time.time()-t0_total)/60.0))
    if "sharpe" in df.columns:
        ok = df[df["sharpe"].notna()]
        if len(ok) > 0:
            top5 = ok.nlargest(5, "sharpe")
            print("\n--- Top 5 by Sharpe ---")
            for _, r in top5.iterrows():
                print("  %s: %.4f (ret=%.2f%%, TO=%.1f)" % (
                    r["config"], r["sharpe"], r["ann_ret"]*100, r["turnover"]))
    cols = [c for c in ["config","sharpe","ann_ret","turnover","max_dd","verdict"] if c in df.columns]
    print("\n" + df[cols].to_string())

if __name__ == "__main__":
    main()
