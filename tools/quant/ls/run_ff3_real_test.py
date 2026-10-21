"""FF3 real-factor residualization test (user research focus, 2026-08-04).

Research question: does predicting the genuine French-Fama risk-adjusted
RESIDUAL return (real Ken French daily factors, not mimicking portfolios)
improve OOS Sharpe vs the demean baseline?

Base = s05_d2 winner config (GBRT d=2, smooth=0.5, demean+zscore, h=10,
n=13, mean_var λ=0.5) at the corrected cost model: 3.8 bps one-side,
slippage 0, no market impact (user spec).

Configs:
  - ff3_real_bw60  (beta_window=60)
  - ff3_real_bw120 (beta_window=120, more stable betas)
  - ff3_proxy      (the old mimicking-portfolio ff3, same base)

Output: tools/quant/ls/results/ff3_real_test/compare_ff3_real.csv
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
    d["slippage_bps"] = 0.0  # corrected cost model (user spec)

    out_dir = os.path.join(RESULTS, "ff3_real_test")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("ff3_real_bw60", {"gbrt_label_residual": "ff3_real",
                           "gbrt_label_ff_beta_window": 60}),
        ("ff3_real_bw120", {"gbrt_label_residual": "ff3_real",
                            "gbrt_label_ff_beta_window": 120}),
        ("ff3_proxy", {"gbrt_label_residual": "ff3"}),
    ]

    import pandas as pd
    rows = []
    for name, over in variants:
        cfg = Config(**{**d, **over})
        cfg.name = name
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = True
        print(f"\n=== {name} ===")
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
        print(row)
        with open(os.path.join(out_dir, f"{name}.config.json"), "w") as f:
            json.dump(cfg.as_dict(), f, indent=2, default=str)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_ff3_real.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_ff3_real.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
