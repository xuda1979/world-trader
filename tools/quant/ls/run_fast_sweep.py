"""Fast focused sweep -- highest-impact configs only."""
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
        ("n_long_8", {"n_long": 8, "n_short": 8}),
        ("tw_160", {"train_window": 160}),
        ("bypass", {"bypass_ic_screen": True}),
        ("depth_1", {"gbrt_max_depth": 1}),
        ("smooth03", {"gbrt_pred_smooth": 0.3}),
        ("mv_l03", {"opt_lambda_risk": 0.3}),
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
        sr = m.get("sharpe", 0) or 0
        ar = float(m.get("annual_return", 0) or 0) * 100
        to = float(m.get("annual_turnover", 0) or 0)
        dd = float(m.get("max_drawdown", 0) or 0) * 100
        row = {"config": name, "sharpe": sr, "ann_ret": ar/100, "turnover": to,
               "max_dd": dd/100, "verdict": v.get("assessment"), "time_s": dt}
        rows.append(row)
        print(f"  Sharpe={sr:.4f} Ret={ar:.1f}% TO={to:.1f} MDD={dd:.1f}% Time={dt:.0f}s", flush=True)

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "compare_fast.csv")
    df.to_csv(csv_path, index=False)
    print(chr(10) + SEP)
    print(f"Done in {time.time()-t_start:.0f}s total.")
    print(chr(10) + "Results:")
    for _, r in df.sort_values("sharpe", ascending=False).iterrows():
        print(f"  {r[chr(34)+chr(99)+chr(111)+chr(110)+chr(102)+chr(105)+chr(103)+chr(34)]:25s} Sharpe={r[chr(34)+chr(115)+chr(104)+chr(97)+chr(114)+chr(112)+chr(101)+chr(34)]:.4f} TO={r[chr(34)+chr(116)+chr(117)+chr(114)+chr(110)+chr(111)+chr(118)+chr(101)+chr(114)+chr(34)]:.1f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
