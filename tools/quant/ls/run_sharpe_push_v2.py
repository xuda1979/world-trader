"""Sharpe push v2 (2026-08-04) -- systematic GBRT exploration.

Base = gbrt_best_repro (Sharpe 1.683, financing ON, 4.8bps, extra_factors=True).
Fixed to user 3.8bps spec (slippage=0).
Sweep: n_long, rebalance_freq, train_window, depth, n_est, lr, smooth, extra_factors, bypass, opt_lambda_risk.
Output: tools/quant/ls/results/sharpe_push_v2/
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner

RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/gbrt_best_repro/config.json")


def main():
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d["slippage_bps"] = 0.0
    d["cost_bps_one_side"] = 3.8

    out_dir = os.path.join(RESULTS, "sharpe_push_v2")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("repro_38bps", {}),
        ("n_long_8", {"n_long": 8, "n_short": 8}),
        ("n_long_12", {"n_long": 12, "n_short": 12}),
        ("n_long_15", {"n_long": 15, "n_short": 15}),
        ("rebal_3", {"rebalance_freq": 3}),
        ("rebal_7", {"rebalance_freq": 7}),
        ("rebal_10", {"rebalance_freq": 10}),
        ("tw_140", {"train_window": 140}),
        ("tw_160", {"train_window": 160}),
        ("tw_180", {"train_window": 180}),
        ("bypass", {"bypass_ic_screen": True}),
        ("depth_1", {"gbrt_max_depth": 1}),
        ("depth_3", {"gbrt_max_depth": 3}),
        ("n100", {"gbrt_n_estimators": 100}),
        ("n400", {"gbrt_n_estimators": 400}),
        ("lr003", {"gbrt_learning_rate": 0.03}),
        ("lr010", {"gbrt_learning_rate": 0.1}),
        ("smooth03", {"gbrt_pred_smooth": 0.3}),
        ("smooth07", {"gbrt_pred_smooth": 0.7}),
        ("no_extra", {"use_extra_factors": False}),
        ("mv_l03", {"opt_lambda_risk": 0.3}),
        ("mv_l05", {"opt_lambda_risk": 0.5}),
        ("mv_l10", {"opt_lambda_risk": 1.0}),
        ("mv_l30", {"opt_lambda_risk": 3.0}),
        ("d1_r3_n8", {"gbrt_max_depth": 1, "rebalance_freq": 3, "n_long": 8, "n_short": 8}),
        ("bypass_tw160", {"bypass_ic_screen": True, "train_window": 160}),
        ("d1_bypass", {"gbrt_max_depth": 1, "bypass_ic_screen": True}),
    ]

    import pandas as pd
    rows = []
    t_start = time.time()

    for name, over in variants:
        cfg = Config(**{**d, **over})
        cfg.name = name
        cfg.out_dir = out_dir
        SEP = "=" * 60
        print(chr(10) + SEP)
        print(f"=== {name} ===", flush=True)
        t0 = time.time()
        res = runner.run(cfg)
        dt = time.time() - t0
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
            "flags": "; ".join(v.get("overfitting_flags", [])),
            "time_s": dt,
        }
        rows.append(row)
        sr = m.get("sharpe", 0) or 0
        ar = float(m.get("annual_return", 0) or 0) * 100
        to = float(m.get("annual_turnover", 0) or 0)
        dd = float(m.get("max_drawdown", 0) or 0) * 100
        print(f"  Sharpe={sr:.4f} Ret={ar:.1f}% TO={to:.1f} MDD={dd:.1f}% Time={dt:.0f}s", flush=True)

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "compare_v2.csv")
    df.to_csv(csv_path, index=False)
    print(chr(10) + SEP)
    print(f"Done in {time.time()-t_start:.0f}s total.")
    print(f"Results -> {csv_path}")
    print(chr(10) + "Sorted by Sharpe:")
    df_sorted = df.sort_values("sharpe", ascending=False)
    for _, r in df_sorted.iterrows():
        print(f"  {r[chr(34)+chr(34).join([chr(99),chr(111),chr(110),chr(102),chr(105),chr(103)])]:25s} Sharpe={r[chr(34)+chr(34).join([chr(115),chr(104),chr(97),chr(114),chr(112),chr(101)])]:.4f} TO={r[chr(34)+chr(34).join([chr(116),chr(117),chr(114),chr(110),chr(111),chr(118),chr(101),chr(114)])]:.1f} {r[chr(34)+chr(34).join([chr(118),chr(101),chr(114),chr(100),chr(105),chr(99),chr(116)])]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
