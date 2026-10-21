"""Sharpe push sweep (2026-08-04) -- user directive: much higher but CORRECT,
realistic Sharpe.

All configs on the RESTORED pipeline (use_ohlc_factors=False, no interaction
features -- matches the verified-reproducible gbrt_tune pipeline) at the
corrected cost model: 3.8 bps one-side, no slippage, no market impact,
call-rate financing on.

Base = s05_d2 winner config (GBRT d=2, smooth=0.5, demean+zscore, h=10,
n=13, mean_var lambda=0.5, vol target 30%).

Levers:
  FF residual (user's French-Fama research focus):
    - ff3_noumd_bw120/bw180: real FF factors minus UMD (keep momentum in
      the label), longer beta windows
  GBRT capacity (correct = shallow + smoothed):
    - gb_n400, gb_lr010, gb_d3_lr003
  Factor breadth (tree feature selection):
    - gb_bypass (all 23 factors), gb_bypass_extra (+extra factors)
  Portfolio levers (net-of-cost):
    - pf_n8 / pf_n5 (concentration), pf_rb20 / pf_rb5 (rebalance freq),
      pf_holdwide (wider hold zone + higher rebalance threshold)

Selection honesty: every config carries diagnostics (window sweep +
factor decay); we report verdicts and do NOT cherry-pick fragile wins.

Output: tools/quant/ls/results/sharpe_push/compare_sharpe_push.csv
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/gbrt_tune/s05_d2/config.json")


def main() -> int:
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["use_ohlc_factors"] = False
    d["use_interaction_features"] = False
    d["use_extra_factors"] = False
    d["slippage_bps"] = 0.0  # corrected cost model

    out_dir = os.path.join(RESULTS, "sharpe_push")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        # --- FF residual, momentum-preserving (user research focus) ---
        ("ff3_noumd_bw120", {"gbrt_label_residual": "ff3_real",
                             "gbrt_label_ff_beta_window": 120,
                             "gbrt_label_ff_factors": "ff3"}),
        ("ff3_noumd_bw180", {"gbrt_label_residual": "ff3_real",
                             "gbrt_label_ff_beta_window": 180,
                             "gbrt_label_ff_factors": "ff3"}),
        # --- GBRT capacity ---
        ("gb_n400", {"gbrt_n_estimators": 400}),
        ("gb_lr010", {"gbrt_learning_rate": 0.1}),
        ("gb_d3_lr003", {"gbrt_max_depth": 3, "gbrt_learning_rate": 0.03}),
        # --- factor breadth via tree feature selection ---
        ("gb_bypass", {"bypass_ic_screen": True}),
        ("gb_bypass_extra", {"bypass_ic_screen": True, "use_extra_factors": True}),
        # --- portfolio levers ---
        ("pf_n8", {"n_long": 8, "n_short": 8}),
        ("pf_n5", {"n_long": 5, "n_short": 5}),
        ("pf_rb20", {"rebalance_freq": 20}),
        ("pf_rb5", {"rebalance_freq": 5}),
        ("pf_holdwide", {"hold_zone_top_pct": 0.05, "hold_zone_bot_pct": 0.05,
                         "turnover_threshold_diff": 0.0012}),
    ]

    import pandas as pd
    rows = []
    for name, over in variants:
        cfg = Config(**{**d, **over})
        cfg.name = name
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = True
        print(f"\n=== {name} ===", flush=True)
        res = runner.run(cfg)
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {
            "config": name,
            "sharpe": m.get("sharpe"),
            "ann_ret": m.get("annual_return"),
            "turnover": m.get("annual_turnover"),
            "max_dd": m.get("max_drawdown"),
            "verdict": v.get("assessment"),
            "n_flags": v.get("n_flags"),
        }
        rows.append(row)
        print(row, flush=True)
        with open(os.path.join(out_dir, f"{name}.config.json"), "w") as f:
            json.dump(cfg.as_dict(), f, indent=2, default=str)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_sharpe_push.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_sharpe_push.csv", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
