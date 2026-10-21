"""Additional model sweep: multi-horizon GBRT, XGBoost, vol-scale labels."""
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
    d.pop("model_method", None)
    d.pop("predict_horizon", None)

    out_dir = os.path.join(RESULTS, "model_sweep")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("mh_d2_h51021", {"model_method": "multihorizon", "gbrt_max_depth": 2, "predict_horizons": [5,10,21]}),
        ("mh_d2_h31021", {"model_method": "multihorizon", "gbrt_max_depth": 2, "predict_horizons": [3,10,21]}),
        ("mh_d1_h51021", {"model_method": "multihorizon", "gbrt_max_depth": 1, "predict_horizons": [5,10,21]}),
        ("xgb_d2", {"model_method": "xgb", "predict_horizon": 10}),
        ("xgb_d3", {"model_method": "xgb", "predict_horizon": 10, "xgb_max_depth": 3}),
        ("xgb_d4", {"model_method": "xgb", "predict_horizon": 10, "xgb_max_depth": 4}),
        ("xgb_d2_lr01", {"model_method": "xgb", "predict_horizon": 10, "xgb_max_depth": 2, "xgb_learning_rate": 0.1}),
        ("xgb_d2_l2", {"model_method": "xgb", "predict_horizon": 10, "xgb_max_depth": 2, "xgb_reg_lambda": 3.0}),
        ("gb_volscale", {"model_method": "gbrt", "predict_horizon": 10, "gbrt_label_vol_scale": True}),
        ("gb_huber", {"model_method": "gbrt", "predict_horizon": 10, "gbrt_loss": "huber"}),
        ("gb_no_label_clip", {"model_method": "gbrt", "predict_horizon": 10, "gbrt_label_winsorize": 0.0}),
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
        sr = m.get("sharpe", 0) or 0
        ar = float(m.get("annual_return", 0) or 0) * 100
        to = float(m.get("annual_turnover", 0) or 0)
        dd = float(m.get("max_drawdown", 0) or 0) * 100
        row = {"config": name, "sharpe": m.get("sharpe"), "ann_ret": m.get("annual_return"),
               "turnover": m.get("annual_turnover"), "max_dd": m.get("max_drawdown"),
               "verdict": v.get("assessment"), "n_flags": v.get("n_flags"),
               "flags": "; ".join(v.get("overfitting_flags", [])), "time_s": dt}
        rows.append(row)
        print(f"  Sharpe={sr:.4f} Ret={ar:.1f}% TO={to:.1f} MDD={dd:.1f}% Time={dt:.0f}s", flush=True)

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "compare_model.csv")
    df.to_csv(csv_path, index=False)
    print(chr(10) + SEP)
    print(f"Done in {time.time()-t_start:.0f}s total. Results -> {csv_path}")

    df_sorted = df.sort_values("sharpe", ascending=False)
    print(chr(10) + "Sorted by Sharpe:")
    for _, r in df_sorted.iterrows():
        print(f"  {r[chr(34)+chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(34)]:25s} Sharpe={r[chr(34)+chr(115)+chr(104)+chr(97)+chr(114)+chr(112)+chr(101)+chr(34)]:.4f}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
