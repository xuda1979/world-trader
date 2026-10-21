#!/usr/bin/env python3
"""Loop-improve harness for the validated LS_GBRT champion (2026-08-11).

User directive:
  - keep improving the champion Sharpe using free datasets
  - LONGER testing window for reliability (20y twelve_liq panel)
  - trading cost = 6 bps one-side (up from 3.8)
  - retrain the model periodically during testing (walk-forward refit)

This script runs the frozen champion config (validation_test/tw320d4_deep_full)
at 6 bps on:
  1. champ_td6   : home panel (twelvedata, 2018-2026) -> cost-impact baseline
  2. champ_liq6  : 20y liquid panel (twelve_liq, OOS from ~2014) -> LONG test
  3. champ_liq6_r5: same long test with refit_freq=5 (fresher model every 5d)

Variants can be added in the IMPROVE phase.  All runs: T+1, call-rate
financing, FRED VIX de-risk, honest trailing-only IC screen.

Usage:
  python -m tools.quant.ls.run_loop_improve
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results", "loop_improve")
CHAMP_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/tw320d4_deep_full/config.json")


def load_champion() -> Config:
    with open(CHAMP_CFG) as f:
        base = json.load(f)
    base.pop("name", None)
    base.pop("out_dir", None)
    # user spec: 6 bps one-side (12 bps round-trip)
    base["cost_bps_one_side"] = 6.0
    base["cost_round_trip_bps"] = 12.0
    return Config(**base)


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    import pandas as pd
    base = load_champion()

    variants = [
        # (name, overrides)
        ("champ_td6", {
            "data_dir": "tools/quant/data/twelvedata",
        }),
        ("champ_liq6", {
            "data_dir": "tools/quant/data/twelve_liq",
            "start_date": "2013-01-01",          # ~13.5y OOS after 320d warmup
        }),
        ("champ_liq6_r5", {
            "data_dir": "tools/quant/data/twelve_liq",
            "start_date": "2013-01-01",
            "refit_freq": 5,                     # fresher model: refit every 5d
        }),
    ]

    rows = []
    for name, over in variants:
        cfg = base.copy(**over)
        cfg.name = name
        cfg.out_dir = RESULTS
        cfg.plot = False
        cfg.save_intermediate = True
        print(f"\n{'='*70}\n=== {name} ===", flush=True)
        t0 = time.time()
        res = runner.run(cfg)
        dt = time.time() - t0
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {
            "config": name,
            "panel": cfg.data_dir.split("/")[-1],
            "start": cfg.start_date or "full",
            "refit_freq": cfg.refit_freq,
            "cost_bps": cfg.cost_bps_one_side,
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

    df = pd.DataFrame(rows)
    out_csv = os.path.join(RESULTS, "compare_loop_improve.csv")
    df.to_csv(out_csv, index=False)
    print(f"\nSaved -> {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
