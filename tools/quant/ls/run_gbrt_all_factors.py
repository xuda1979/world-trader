"""GBRT with all 23 factors (bypass ICIR screen) — sweep depth / n_estimators.

Hypothesis: ICIR screen discards factors that GBRT can exploit via nonlinear
interactions. Tree models are natural feature selectors.

Sweep: max_depth ∈ {1, 2, 3} × n_estimators ∈ {200, 500, 1000}
       × learning_rate ∈ {0.01, 0.03, 0.05}
29 configs (27 + 2 depth=1 high-n special cases).
"""
from __future__ import annotations
import os, sys, time, itertools

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls import runner
from tools.quant.ls.config import Config
import pandas as pd

BASE = {
    "model_method": "gbrt",
    "bypass_ic_screen": True,  # ALL 23 factors go to GBRT
    # GBRT params
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
    "gbrt_loss": "squared_error",
    # All extra factors ON
    "use_extra_factors": True,
    # Portfolio construction
    "n_long": 10, "n_short": 10, "use_fixed_n": True,
    "weighting": "mean_var", "opt_lambda_risk": 0.5,
    "position_cap_pct": 0.20, "gross_leverage": 1.6,
    "max_gross_leverage": 1.6, "vol_target_active": False,
    "long_short_balance": True, "beta_target": 0.0, "beta_max_abs": 0.05,
    # Execution
    "train_window": 120, "refit_freq": 5, "rebalance_freq": 5,
    "predict_horizon": 10, "return_horizon_fwd": 10,
    "t_plus_1": True, "cost_bps_one_side": 3.8, "slippage_bps": 1.0,
    # Financing
    "use_call_rate_financing": True, "short_borrow_apply": True,
    "long_financing_apply": True,
    "short_rebate_paid_bps": 150.0, "short_borrow_fee_etb_bps": 25.0,
    "long_financing_spread_bps": 50.0,
    # Output
    "save_intermediate": False, "plot": False, "verbose": False,
}

def run_config(name, **overrides):
    cfg_dict = dict(BASE, name=name, **overrides)
    cfg_dict["out_dir"] = "tools/quant/ls/results/gbrt_all_factors/" + name
    cfg = Config.from_dict(cfg_dict)
    t0 = time.time()
    try:
        bundle = runner.run(cfg, export=True)
        dt = time.time() - t0
        m = bundle["metrics"]
        verdict = bundle["diagnostics"]["verdict"]
        return {
            "config": name,
            "depth": overrides.get("gbrt_max_depth", BASE["gbrt_max_depth"]),
            "n_est": overrides.get("gbrt_n_estimators", BASE["gbrt_n_estimators"]),
            "lr": overrides.get("gbrt_learning_rate", BASE["gbrt_learning_rate"]),
            "sharpe": m.get("sharpe", 0),
            "ann_ret": m.get("annual_return", 0),
            "ann_vol": m.get("annual_volatility", 0),
            "turnover": m.get("annual_turnover", 0),
            "max_dd": m.get("max_drawdown", 0),
            "sortino": m.get("sortino_ratio", 0),
            "verdict": verdict["assessment"],
            "n_flags": verdict["n_flags"],
            "n_kept": len(bundle["kept_factors"]),
            "runtime_s": dt,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"config": name, "error": str(e), "runtime_s": time.time() - t0}

def main():
    depths = [1, 2, 3]
    n_estims = [200, 500, 1000]
    lrs = [0.01, 0.03, 0.05]
    grid = list(itertools.product(depths, n_estims, lrs))
    # Decision stumps (depth=1) need more trees
    grid += [(1, 2000, 0.01), (1, 2000, 0.03)]
    print("=== GBRT ALL-FACTORS SWEEP: %d configs ===" % len(grid))

    results = []
    t0_total = time.time()
    for i, (d, n, lr) in enumerate(grid):
        name = "all_d%d_n%d_lr%.3f" % (d, n, lr)
        print("\n[%d/%d] %s" % (i+1, len(grid), name))
        r = run_config(name,
                       gbrt_max_depth=d, gbrt_n_estimators=n,
                       gbrt_learning_rate=lr)
        results.append(r)
        if "sharpe" in r:
            print("  Sharpe=%.4f  AnnRet=%.4f  Vol=%.4f  TO=%.1f  DD=%.3f  %s(%d)  nf=%d  dt=%ds" % (
                r["sharpe"], r["ann_ret"], r["ann_vol"], r["turnover"],
                r["max_dd"], r["verdict"], r["n_flags"],
                r["n_kept"], int(r["runtime_s"])))
        else:
            print("  ERROR: %s" % r.get("error", "?"))

    df = pd.DataFrame(results)
    out_dir = os.path.join(ROOT, "tools/quant/ls/results/gbrt_all_factors")
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "_summary.csv"), index=False)
    dt_total = int(time.time() - t0_total)
    print("\n=== DONE in %.1f min ===" % (dt_total/60.0))
    if "sharpe" in df.columns:
        ok = df[df["sharpe"].notna()]
        if len(ok) > 0:
            best = ok.loc[ok["sharpe"].idxmax()]
            print("BEST: %s  Sharpe=%.4f  AnnRet=%.4f  Vol=%.4f" % (
                best["config"], best["sharpe"], best["ann_ret"], best["ann_vol"]))
            # Top 5
            top5 = ok.nlargest(5, "sharpe")
            print("\nTop 5:")
            for _, row in top5.iterrows():
                print("  %-35s Sharpe=%.4f  Ret=%.4f  TO=%.1f" % (
                    row["config"], row["sharpe"], row["ann_ret"], row["turnover"]))
    cols = [c for c in ["config","sharpe","ann_ret","ann_vol","turnover","max_dd","verdict","n_flags"] if c in df.columns]
    print("\n" + df[cols].to_string())

if __name__ == "__main__":
    main()
