#!/usr/bin/env python3
"""Loop-improve phase 3: longer-window + retraining-cadence tests of the
8y winner (champ_td6_h21_n13, SR 1.202 @6bps).

Directive (2026-08-12): keep improving champion Sharpe; LONGER test window
for reliability; 6 bps one-side cost; periodic retraining (refit cadence).

Key questions this phase answers:
  1. w20y     : does the IMPROVED config (h21+n13) survive the 20y window
                on the 86-name twelvedata panel?  (Earlier 20y failures used
                the OLD champion config -> negative OOS IC.)
  2. w20y_fx  : 20y with the factor set FORCED to the 8y winners
                (mom_12m, mom_12_1m, vol_60d via factor_exclude).  Tests the
                hypothesis that the trailing IC screen's selection on longer
                history (e.g. sign-flipped liq_turnover) causes the IC collapse.
  3. w8y_r4   : winner config, refit_freq=4 (fresher retrain every 4d vs 10d)
                on the 8y panel -- user: "model not too old".
  4. w8y_r20  : winner config, refit_freq=20 (older model) -- control.

Usage:
  python -m tools.quant.ls.run_loop_improve3 [variant...]
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results", "loop_improve")
WINNER_CFG = os.path.join(ROOT, "tools/quant/ls/results/loop_improve/champ_td6_h21_n13/config.json")

# 8y-winner factor set (kept by the 8y trailing screen): everything else excluded
FORCE_8Y_FACTORS = tuple(
    "mom_1m mom_3m mom_6m high_dist reversal_1w reversal_3w skew_60d "
    "ma_dev_200 ma_dev_50 vol_surprise liq_turnover".split()
)

VARIANTS = {
    "w20y": {
        "start_date": "2013-01-01",          # ~13.5y OOS after 320d warmup
    },
    "w20y_fx": {
        "start_date": "2013-01-01",
        "factor_exclude": FORCE_8Y_FACTORS,  # force the 8y winning factor set
    },
    "w8y_r4": {
        "refit_freq": 4,                     # fresher retrain every 4d
    },
    "w8y_r20": {
        "refit_freq": 20,                    # older model control
    },
    "w8y_r2": {
        "refit_freq": 2,                     # freshest: refit every 2d
    },
    "w8y_r4_vix32": {
        "refit_freq": 4,
        "vix_derisk_factor": 1.0,            # swap percentile gate for stress gate
        "vix_level_threshold": 32.0,
        "vix_level_factor": 0.3,
    },
    "w10y": {
        "start_date": "2016-01-01",          # intermediate window between 8y and 20y
        "refit_freq": 4,
    },
}


def main() -> int:
    os.makedirs(RESULTS, exist_ok=True)
    with open(WINNER_CFG) as f:
        base = json.load(f)
    base.pop("name", None)
    base.pop("out_dir", None)
    base_cfg = Config(**base)

    want = sys.argv[1:] or list(VARIANTS)
    for name in want:
        over = VARIANTS[name]
        cfg = base_cfg.copy(**over)
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
        oos_ic = res.get("predictions", {}).get("oos_ic_mean")
        ic_str = f"OOSIC={oos_ic:.4f}" if oos_ic is not None else "OOSIC=n/a"
        print(f"RESULT {name} sharpe={m.get('sharpe'):.3f} ret={m.get('annual_return'):.3f} "
              f"dd={m.get('max_drawdown'):.3f} to={m.get('annual_turnover'):.1f} "
              f"n_days={m.get('n_days')} verdict={v.get('assessment')} "
              f"{ic_str} wall={dt/60:.1f}min", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
