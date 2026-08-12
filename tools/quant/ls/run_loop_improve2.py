#!/usr/bin/env python3
"""Loop-improve phase 2: champion-perturbation sweep on the LONG 20y panel.

All variants: champion tw320_d4 config, twelve_liq (2013-2026, ~13y OOS),
6 bps one-side, periodic walk-forward refit (refit_freq 10 unless overridden).

Levers at 6 bps (12 bps round-trip) vs the 3.8 bps-optimized champion:
  1. tth12     : swap no-trade band scaled to cost (0.0012 vs 0.0008)
  2. h21       : Novy-Marx 21d horizon + 21d rebalance (optimal at higher RT cost)
  3. vix32     : single VIX>=32/0.3 stress gate (best verified risk filter)
  4. smooth7   : stronger pred EMA smoothing (0.7) -> less churn at higher cost
  5. n20       : 20+20 names (more breadth on the 120-name universe)

Usage:
  python -m tools.quant.ls.run_loop_improve2 [variant...]
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results", "loop_improve_sweep")
CHAMP_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/tw320d4_deep_full/config.json")

VARIANTS = {
    "liq6_tth12": {"turnover_threshold_diff": 0.0012},
    "liq6_h21": {"return_horizon_fwd": 21, "predict_horizon": 21, "rebalance_freq": 21},
    "liq6_vix32": {"vix_derisk_factor": 1.0, "vix_level_threshold": 32.0, "vix_level_factor": 0.3},
    "liq6_smooth7": {"gbrt_pred_smooth": 0.7},
    "liq6_n20": {"n_long": 20, "n_short": 20},
}

BASE_OVERRIDES = {
    "data_dir": "tools/quant/data/twelve_liq",
    "start_date": "2013-01-01",
    "cost_bps_one_side": 6.0,
    "cost_round_trip_bps": 12.0,
}


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    with open(CHAMP_CFG) as f:
        base = json.load(f)
    base.pop("name", None)
    base.pop("out_dir", None)
    base.update(BASE_OVERRIDES)
    base_cfg = Config(**base)

    want = sys.argv[1:] or list(VARIANTS)
    rows = []
    for name in want:
        over = VARIANTS[name]
        cfg = base_cfg.copy(**over)
        cfg.name = name
        cfg.out_dir = RESULTS
        cfg.plot = False
        cfg.save_intermediate = False  # sweep: keep it light
        print(f"\n{'='*70}\n=== {name} ===", flush=True)
        t0 = time.time()
        res = runner.run(cfg)
        dt = time.time() - t0
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {
            "config": name,
            "sharpe": m.get("sharpe"),
            "ann_ret": m.get("annual_return"),
            "ann_vol": m.get("annual_volatility"),
            "turnover": m.get("annual_turnover"),
            "max_dd": m.get("max_drawdown"),
            "n_days": m.get("n_days"),
            "verdict": v.get("assessment"),
            "n_flags": v.get("n_flags"),
            "wall_sec": round(dt, 0),
        }
        rows.append(row)
        print(row, flush=True)

    import pandas as pd
    df = pd.DataFrame(rows)
    out_csv = os.path.join(RESULTS, "compare_sweep.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved -> {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
