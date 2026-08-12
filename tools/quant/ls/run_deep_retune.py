"""Deep-panel retune harness (OOS>3 pursuit, 2026-08-04).

When a longer panel lands (Twelve Data 4y fetch once the day quota resets,
or any future data_dir), re-tune the champion's capacity levers that need
statistical power: deeper GBRT, longer train window, more names, 20d
horizon.  All runs use the honest trailing-only screen (screen_trailing_only)
and realistic costs (3.8 bps one-side, slippage 0, no market impact).

Usage:
  python -m tools.quant.ls.run_deep_retune [data_dir]
Default data_dir = tools/quant/data/polygon (works now; pass the Twelve
Data dir when it's ready).

Output: results/deep_retune/compare_deep_retune.csv
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/d3r10n15g4_full/config.json")


def main() -> int:
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "tools/quant/data/polygon"
    with open(SRC_CFG) as f:
        base = json.load(f)
    base.pop("name", None)
    base.pop("out_dir", None)
    base["slippage_bps"] = 0.0
    base["screen_trailing_only"] = True  # honest screening
    if "twelvedata" in data_dir:
        base["universe_min_avg_vol"] = 0.0  # free tier returns vol=0; liq factor drops via screen

    variants = [
        ("champion_trail", {}),                       # baseline on this panel
        ("d3", {"gbrt_max_depth": 3}),
        ("d4", {"gbrt_max_depth": 4}),
        ("d5", {"gbrt_max_depth": 5}),
        ("tw260", {"train_window": 260}),
        ("tw320_d4", {"train_window": 320, "gbrt_max_depth": 4}),
        ("tw500_d4", {"train_window": 500, "gbrt_max_depth": 4}),
        ("n20", {"n_long": 20, "n_short": 20}),
        ("n26", {"n_long": 26, "n_short": 26}),
        ("rb15", {"rebalance_freq": 15}),
        ("rb25", {"rebalance_freq": 25}),
    ]

    out_dir = os.path.join(RESULTS, "deep_retune")
    os.makedirs(out_dir, exist_ok=True)

    import pandas as pd
    rows = []
    for name, over in variants:
        cfg = Config(**{**base, **over})
        cfg.data_dir = data_dir
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
            "ann_vol": m.get("annual_volatility"),
            "turnover": m.get("annual_turnover"),
            "max_dd": m.get("max_drawdown"),
            "verdict": v.get("assessment"),
            "n_flags": v.get("n_flags"),
        }
        rows.append(row)
        print(row, flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_deep_retune.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_deep_retune.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
