"""Iteration 3 sweep (2026-08-04) -- combine d3+CAPM-alpha champion with proven
orthogonal levers + test new model families.

BASE: champ_d3_mkt_bw120 (SR=2.316, gbrt d=3, mkt-only CAPM-alpha label,
rb20/tw160, lev=1.0, vol_target=0.30, no trend gate).

Orthogonal levers (proven additive):
  - Trend-gate flat (60d SPY < -5%) -- added +0.12 to d=2 demean champ
  - Trend-gate flat40 (40d SPY < -5%) -- shorter lookback
  - Higher vol target (0.40) -- scales returns linearly

Unexplored model variants:
  - d=4 CAPM-alpha (depth experiment)
  - GBRT+RF ensemble / RF-only -- prediction variance reduction
  - subsample=0.7 (stochastic GB, reduces overfit)
  - huber loss (robust to fat tails)

Cross-combinations: tg_flat60 + d4 / extra_factors / subsample / huber

XGBoost variants: skipped (not installed). Install: pip install xgboost

Output: tools/quant/ls/results/iter3_sweep/
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner
import pandas as pd

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/iter2_probes/champ_d3_mkt_bw120/config.json")


def main() -> int:
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["use_ohlc_factors"] = False
    d["use_interaction_features"] = False
    d["use_v2_factors"] = False
    d["slippage_bps"] = 0.0

    out_dir = os.path.join(RESULTS, "iter3_sweep")
    os.makedirs(out_dir, exist_ok=True)

    # --- Trend gate variants on d3 base ---
    tg_variants = [
        ("d3_base", {"trend_gate_enabled": False}),
        ("d3_tg_flat60", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                          "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0}),
        ("d3_tg_flat40", {"trend_gate_enabled": True, "trend_gate_lookback": 40,
                          "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0}),
        ("d3_tg_half60", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                          "trend_gate_threshold": -0.05, "trend_gate_factor": 0.5}),
    ]

    # --- Model architecture variants ---
    model_variants = [
        ("d4_mkt_bw120", {"gbrt_max_depth": 4}),
        ("d3_mkt_bw60", {"gbrt_label_ff_beta_window": 60}),
        ("d3_mkt_bw252", {"gbrt_label_ff_beta_window": 252}),
        ("d3_sub07", {"gbrt_subsample": 0.7}),
        ("d3_huber", {"gbrt_loss": "huber"}),
        ("d3_presmooth03", {"gbrt_pred_smooth": 0.3}),
    ]

    # --- New model families ---
    new_model_variants = [
        ("ensemble_d3", {"model_method": "ensemble", "gbrt_max_depth": 3,
                         "rf_max_depth": 3, "rf_n_estimators": 500}),
        ("rf_d3_base", {"model_method": "rf", "rf_max_depth": 3,
                        "rf_n_estimators": 500, "rf_min_samples_leaf": 20,
                        "rf_max_features": "sqrt"}),
    ]

    # --- Cross-combinations: tg_flat60 x model variants ---
    cross_variants = [
        ("d3_tg_d4", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                      "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                      "gbrt_max_depth": 4}),
        ("d3_tg_extra", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                         "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                         "use_extra_factors": True}),
        ("d3_tg_sub07", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                         "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                         "gbrt_subsample": 0.7}),
        ("d3_tg_huber", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                         "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                         "gbrt_loss": "huber"}),
    ]

    # --- Factor breadth ---
    factor_variants = [
        ("d3_extra", {"use_extra_factors": True}),
        ("d3_icir005", {"icir_threshold": 0.05, "ic_mean_threshold": 0.005}),
        ("d3_bypass_extra", {"bypass_ic_screen": True, "use_extra_factors": True}),
    ]

    # --- Higher vol target (linear scaling test) ---
    vol_variants = [
        ("d3_tg_vt40", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                        "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                        "vol_target_annual": 0.40, "max_gross_leverage": 2.0}),
        ("d3_tg_vt50", {"trend_gate_enabled": True, "trend_gate_lookback": 60,
                        "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
                        "vol_target_annual": 0.50, "max_gross_leverage": 2.5}),
    ]

    all_variants = (tg_variants + model_variants + new_model_variants +
                    cross_variants + factor_variants + vol_variants)

    rows = []
    t_total = time.time()

    for i, (name, over) in enumerate(all_variants):
        cfg = Config(**{**d, **over})
        cfg.name = name
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = False
        t0 = time.time()
        print(f"[{i+1}/{len(all_variants)}] {name}", flush=True)
        try:
            res = runner.run(cfg)
            dt = time.time() - t0
            m = res.get("metrics", {})
            v = res.get("diagnostics", {}).get("verdict", {})
            row = {
                "config": name, "sharpe": m.get("sharpe"),
                "ann_ret": m.get("annual_return"),
                "ann_vol": m.get("annual_volatility"),
                "turnover": m.get("annual_turnover"),
                "max_dd": m.get("max_drawdown"),
                "win_rate": m.get("win_rate"),
                "avg_gross_exp": m.get("avg_gross_exposure"),
                "verdict": v.get("assessment"),
                "n_flags": v.get("n_flags"),
                "flags": "; ".join(v.get("overfitting_flags", [])),
                "runtime_s": dt,
                "n_risk_events": m.get("n_risk_events", 0),
            }
            rows.append(row)
            print(f"  SR={m.get('sharpe', 0):.4f}  "
                  f"Ret={float(m.get('annual_return', 0))*100:.1f}%  "
                  f"Vol={float(m.get('annual_volatility', 0))*100:.1f}%  "
                  f"TO={m.get('annual_turnover', 0):.1f}  "
                  f"DD={float(m.get('max_drawdown', 0))*100:.1f}%  "
                  f"gross_exp={float(m.get('avg_gross_exposure', 0))*100:.1f}%  "
                  f"{v.get('assessment', '?')}({v.get('n_flags', 99)}f)  dt={dt:.0f}s",
                  flush=True)
            with open(os.path.join(out_dir, f"{name}.config.json"), "w") as f:
                json.dump(cfg.as_dict(), f, indent=2, default=str)
        except Exception as e:
            import traceback
            traceback.print_exc()
            rows.append({"config": name, "error": str(e),
                         "runtime_s": time.time() - t0})

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "compare_iter3.csv")
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_total) / 60
    print(f"\nDONE in {dt_total:.1f} min. -> {csv_path}")

    ok = [r for r in rows if "sharpe" in r and r["sharpe"] and r["sharpe"] > 0]
    ok.sort(key=lambda x: x["sharpe"], reverse=True)
    print("\nTOP CONFIGS:")
    for r in ok[:20]:
        print(f"  {r['config']:30s} SR={r['sharpe']:.4f}  "
              f"Ret={float(r['ann_ret'])*100:.1f}%  "
              f"Vol={float(r['ann_vol'])*100:.1f}%  "
              f"TO={r.get('turnover', 0):.1f}  "
              f"DD={float(r.get('max_dd', 0))*100:.1f}%  "
              f"gross={float(r.get('avg_gross_exp', 0))*100:.1f}%  "
              f"{r.get('verdict', '?')}({r.get('n_flags', '?')}f)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
