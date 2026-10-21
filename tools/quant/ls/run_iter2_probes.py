"""Iteration 2 probes (2026-08-04) at the champion base rb20_tw160.

Base = s05_d2 winner config + rebalance_freq=20 + train_window=160 +
slippage=0 (3.8bps) + OHLC/interaction/extra factors off (restored pipeline).

Probes:
  1. champ_mkt_bw120 / bw60 -- CAPM-alpha label: residualize forward return
     against real FF Mkt-RF only (gbrt_label_ff_factors='mkt'). The purest
     "French-Fama risk-adjusted residual" that keeps momentum/size/value
     cross-sectional signal intact (unlike the UMD stripping that killed
     the momentum edge in iteration 1).
  2. champ_mh_51021 / champ_mh_510 / champ_mh_1021 -- IC-weighted
     multi-horizon GBRT blend (models_extra.roll_forward_multihorizon):
     h in predict_horizons, weights by rolling OOS IC. Exploits the
     h=5 vs h=10 prediction correlation (~0.53) -- the real diversification
     lever identified in the ensemble work.

Output: tools/quant/ls/results/iter2_probes/compare_iter2.csv
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
    d.update(use_ohlc_factors=False, use_interaction_features=False,
             use_extra_factors=False, slippage_bps=0.0,
             rebalance_freq=20, train_window=160)

    out_dir = os.path.join(RESULTS, "iter2_probes")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("champ_mkt_bw120", {"gbrt_label_residual": "ff3_real",
                             "gbrt_label_ff_factors": "mkt",
                             "gbrt_label_ff_beta_window": 120}),
        ("champ_mkt_bw60", {"gbrt_label_residual": "ff3_real",
                            "gbrt_label_ff_factors": "mkt",
                            "gbrt_label_ff_beta_window": 60}),
        ("champ_mh_51021", {"model_method": "multihorizon",
                            "predict_horizons": (5, 10, 21)}),
        ("champ_mh_510", {"model_method": "multihorizon",
                          "predict_horizons": (5, 10)}),
        ("champ_mh_1021", {"model_method": "multihorizon",
                           "predict_horizons": (10, 21)}),
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
    df.to_csv(os.path.join(out_dir, "compare_iter2.csv"), index=False)
    print(f"\nSaved -> {out_dir}/compare_iter2.csv", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
