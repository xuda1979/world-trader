"""Re-run best configs with the corrected cost model (user spec 2026-08-04).

User clarification: trading cost = 3.8 bps one-side, NO market impact, NO
slippage.  The previous gbrt_tune / ensemble runs used slippage_bps=1.0
(effective 4.8 bps/side).  This script loads the saved winner configs,
sets slippage_bps=0.0, and re-runs them so all Sharpe numbers are on the
same corrected cost basis.

Configs (from results/gbrt_tune/*/config.json):
  - s05_d2   (GBRT d=2, smooth=0.5, demean+zscore, Sharpe 1.237 @4.8bps)
  - s03_d2   (GBRT d=2, smooth=0.3, Sharpe 1.191)
  - base_s05_d3 (GBRT d=3, smooth=0.5, Sharpe 0.973)
  - icir_mv_l05 equivalent at same base (ICIR, mean_var λ=0.5, Sharpe 0.651)

Output: tools/quant/ls/results/cost38_rerun/
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")


def load_config(path: str) -> Config:
    with open(path) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    return Config(**d)


def main() -> int:
    src = [
        ("s05_d2", "results/gbrt_tune/s05_d2/config.json"),
        ("s03_d2", "results/gbrt_tune/s03_d2/config.json"),
        ("base_s05_d3", "results/gbrt_tune/base_s05_d3/config.json"),
    ]
    out_dir = os.path.join(RESULTS, "cost38_rerun")
    os.makedirs(out_dir, exist_ok=True)

    rows = []
    for name, rel in src:
        cfg = load_config(os.path.join(ROOT, "tools/quant/ls", rel))
        cfg.name = f"{name}_cost38"
        cfg.slippage_bps = 0.0
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = True
        print(f"\n=== Re-running {name} at 3.8bps (no slippage) ===")
        res = runner.run(cfg)
        m = res.get("metrics", {})
        v = res.get("diagnostics", {}).get("verdict", {})
        row = {
            "config": cfg.name,
            "sharpe": m.get("sharpe", float("nan")),
            "ann_ret": m.get("annual_return", float("nan")),
            "turnover": m.get("annual_turnover", float("nan")),
            "max_dd": m.get("max_drawdown", float("nan")),
            "verdict": v.get("assessment", ""),
            "n_flags": v.get("n_flags", ""),
        }
        rows.append(row)
        print(row)
        # stash config for reproducibility
        with open(os.path.join(out_dir, f"{cfg.name}.config.json"), "w") as f:
            json.dump(cfg.to_dict() if hasattr(cfg, "to_dict") else cfg.__dict__,
                      f, indent=2, default=str)

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(out_dir, "compare_cost38.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_cost38.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
