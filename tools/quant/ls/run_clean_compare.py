"""Clean unified comparison on the restored pipeline (2026-08-04).

Background: a concurrent session added OHLC + interaction factor libraries
and accidentally left a duplicate `use_ohlc_factors` config field (False
then True), flipping the effective default to True.  That silently changed
every run's factor set vs the Aug 3 gbrt_tune results (s05_d2 1.237).
This script pins the experimental factor flags OFF and re-runs the exact
winner config to (a) verify reproducibility, (b) answer the cost question
(3.8bps, no slippage, no impact -- user spec), (c) test real FF-factor
residualization (user's French-Fama research focus).

Variants (all = s05_d2 base config):
  1. repro_slip10   slippage=1.0, demean   -> expect ~1.237 (repro check)
  2. cost38_demean  slippage=0.0, demean   -> true cost A/B
  3. ff3_real_bw60  slippage=0.0, ff3_real (beta_window=60)
  4. ff3_real_bw120 slippage=0.0, ff3_real (beta_window=120)
  5. ff3_proxy      slippage=0.0, ff3 (mimicking portfolios, reference)

Output: tools/quant/ls/results/clean_compare/compare_clean.csv
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
    # Pin experimental factor libraries OFF (restore Aug 3 pipeline)
    d["use_ohlc_factors"] = False
    d["use_interaction_features"] = False
    d["use_extra_factors"] = False

    out_dir = os.path.join(RESULTS, "clean_compare")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("repro_slip10", {"slippage_bps": 1.0, "gbrt_label_residual": "demean"}),
        ("cost38_demean", {"slippage_bps": 0.0, "gbrt_label_residual": "demean"}),
        ("ff3_real_bw60", {"slippage_bps": 0.0, "gbrt_label_residual": "ff3_real",
                           "gbrt_label_ff_beta_window": 60}),
        ("ff3_real_bw120", {"slippage_bps": 0.0, "gbrt_label_residual": "ff3_real",
                            "gbrt_label_ff_beta_window": 120}),
        ("ff3_proxy", {"slippage_bps": 0.0, "gbrt_label_residual": "ff3"}),
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
    df.to_csv(os.path.join(out_dir, "compare_clean.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_clean.csv", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
