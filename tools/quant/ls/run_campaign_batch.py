"""Generic Sharpe-campaign batch runner (OOS>3 pursuit, 2026-08-04).

Loads variants from results/sharpe_campaign/batch_variants.json:
  [{"name": "smooth07", "overrides": {"gbrt_pred_smooth": 0.7}}, ...]
Runs each at the frozen champion base (validation_test/mkt_full) with the
realistic cost model (3.8 bps one-side, slippage 0, no market impact),
appends rows to results/sharpe_campaign/compare_campaign.csv.

Usage:  python -m tools.quant.ls.run_campaign_batch
"""
from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")
CAMPAIGN_DIR = os.path.join(RESULTS, "sharpe_campaign")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/validation_test/tw320d4_deep_full/config.json")
VARIANTS_FILE = os.path.join(CAMPAIGN_DIR, "batch_variants.json")
CSV_FILE = os.path.join(CAMPAIGN_DIR, "compare_campaign.csv")


def main() -> int:
    with open(SRC_CFG) as f:
        base = json.load(f)
    base.pop("name", None)
    base.pop("out_dir", None)
    base["slippage_bps"] = 0.0  # realistic cost model (user spec)

    with open(VARIANTS_FILE) as f:
        variants = json.load(f)

    os.makedirs(CAMPAIGN_DIR, exist_ok=True)

    import pandas as pd
    rows = []
    for v in variants:
        name = v["name"]
        cfg = Config(**{**base, **v.get("overrides", {})})
        cfg.name = name
        cfg.out_dir = CAMPAIGN_DIR
        cfg.plot = False
        cfg.verbose = True
        print(f"\n=== {name} ===")
        res = runner.run(cfg)
        m = res.get("metrics", {})
        diag = res.get("diagnostics", {})
        vrd = diag.get("verdict", {})
        row = {
            "config": name,
            "sharpe": m.get("sharpe"),
            "ann_ret": m.get("annual_return"),
            "ann_vol": m.get("annual_volatility"),
            "turnover": m.get("annual_turnover"),
            "max_dd": m.get("max_drawdown"),
            "verdict": vrd.get("assessment"),
            "n_flags": vrd.get("n_flags"),
            "overnight_ic": diag.get("overnight_ic"),
        }
        # half-sample splits if present
        for k in ("split_hi", "split_lo", "split_first", "split_second"):
            if k in diag:
                row[k] = diag[k]
        rows.append(row)
        print(row)
        with open(os.path.join(CAMPAIGN_DIR, f"{name}.config.json"), "w") as f:
            json.dump(cfg.as_dict(), f, indent=2, default=str)

    df = pd.DataFrame(rows)
    if os.path.exists(CSV_FILE):
        old = pd.read_csv(CSV_FILE)
        df = pd.concat([old, df], ignore_index=True).drop_duplicates(
            subset=["config"], keep="last")
    df.to_csv(CSV_FILE, index=False)
    print(f"\nSaved -> {CSV_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
