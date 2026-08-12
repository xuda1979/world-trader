"""Portfolio diversification grid at the frozen champion base (OOS>3 pursuit,
2026-08-04).

Research question: does holding MORE names (13L/13S -> 20L/20S, 26L/26S)
raise OOS Sharpe by diversifying idiosyncratic risk at fixed gross?

Base = champion config (validation_test/mkt_full: ff3_real mkt-label bw60,
tw160, rb20, mean_var lambda=0.5, trend gate) at realistic costs:
3.8 bps one-side, slippage 0, no market impact (user spec).

Configs:
  - n13_repro  (exact champion; expected ~2.11 Sharpe, sanity check)
  - n20        (20L/20S)
  - n26        (26L/26S)

Output: tools/quant/ls/results/n_names/compare_n_names.csv
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/mkt_full/config.json")


def main() -> int:
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["slippage_bps"] = 0.0  # corrected cost model (user spec)

    out_dir = os.path.join(RESULTS, "n_names")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("n13_repro", {}),
        ("n20", {"n_long": 20, "n_short": 20}),
        ("n26", {"n_long": 26, "n_short": 26}),
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
            "ann_vol": m.get("annual_volatility"),
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
    df.to_csv(os.path.join(out_dir, "compare_n_names.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_n_names.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
