"""Real French-Fama BETA features test (research axis: the 'french beth'
factors model, 2026-08-04).

Research question: do stock-level trailing loadings on the PUBLISHED Ken
French factors (Mkt-RF, SMB, HML, UMD) -- used as cross-sectional PREDICTOR
features, on top of the champion's CAPM-alpha (ff3_real/mkt) label --
improve OOS Sharpe vs the frozen champion?

Base = champion config (validation_test/mkt_full: ff3_real mkt-label bw60,
tw160, rb20, 13L/13S, mean_var lambda=0.5, trend gate) at realistic costs:
3.8 bps one-side, slippage 0, no market impact (user spec).

Configs:
  - champion_repro  (exact champion; expected ~2.11 Sharpe, sanity check)
  - ffbeta_bw120    (+ FF-beta features, 120d beta window)
  - ffbeta_bw60     (+ FF-beta features, 60d beta window, matches label bw)

Output: tools/quant/ls/results/ff_beta_features/compare_ff_beta.csv
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

    out_dir = os.path.join(RESULTS, "ff_beta_features")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("champion_repro", {}),
        ("ffbeta_bw120", {"use_ff_beta_factors": True}),
        ("ffbeta_bw60", {"use_ff_beta_factors": True, "ff_beta_window": 60}),
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
    df.to_csv(os.path.join(out_dir, "compare_ff_beta.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_ff_beta.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
