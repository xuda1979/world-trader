"""Trend gate parameter sweep + XGBoost test (2026-08-04).

Bear-regime Sharpe is -1.6 in ALL configs. The trend gate is wired in backtest.py
but never swept. First test (tg_flat60, default params) pushed Sharpe from 2.146
to 2.269. This sweep finds the optimal gate parameters and combines with XGBoost.
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/trend_gate_test/tg_flat60.config.json")


def compute_block_sharpe(daily_csv_path, rebalance_freq):
    """Compute honest block Sharpe on non-overlapping rebalance periods."""
    import pandas as pd
    import numpy as np
    df = pd.read_csv(daily_csv_path, index_col=0).squeeze()
    n = len(df)
    blocks = []
    for i in range(0, n, rebalance_freq):
        block = df.iloc[i:min(i + rebalance_freq, n)]
        if len(block) >= max(3, rebalance_freq // 2):
            blocks.append((1 + block).prod() - 1)
    if len(blocks) < 5:
        return {"block_sharpe": np.nan, "n_blocks": len(blocks), "t_stat": np.nan}
    arr = np.array(blocks)
    mu = arr.mean()
    sd = arr.std(ddof=1)
    if sd == 0:
        return {"block_sharpe": np.nan, "n_blocks": len(arr), "t_stat": np.nan}
    ann_sr = (mu / sd) * np.sqrt(252 / rebalance_freq)
    t_stat = mu / (sd / np.sqrt(len(arr)))
    return {"block_sharpe": float(ann_sr), "n_blocks": len(arr), "t_stat": float(t_stat)}


def main():
    with open(SRC_CFG) as f:
        d = json.load(f)
    d.pop("name", None)
    d.pop("out_dir", None)
    d.update(
        use_ohlc_factors=False,
        use_interaction_features=False,
        use_extra_factors=False,
        slippage_bps=0.0,
        cost_bps_one_side=3.8,
    )

    out_dir = os.path.join(RESULTS, "trend_gate_sweep")
    os.makedirs(out_dir, exist_ok=True)

    # ---- Phase 1: trend gate parameter grid ----
    lookbacks = [20, 40, 60, 80, 100, 120]
    thresholds = [-0.03, -0.05, -0.07, -0.10]

    phase1_variants = []
    for lb in lookbacks:
        for th in thresholds:
            name = "tg_lb%d_th%02d" % (lb, int(abs(th)*100))
            over = {
                "trend_gate_enabled": True,
                "trend_gate_lookback": lb,
                "trend_gate_threshold": th,
                "trend_gate_factor": 0.0,
            }
            phase1_variants.append((name, over))

    # ---- Phase 2: best gate + XGBoost ----
    phase2_variants = [
        ("tg_xgb_lb60_th05", {
            "trend_gate_enabled": True, "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
            "model_method": "xgb",
        }),
        ("tg_xgb_lb40_th05", {
            "trend_gate_enabled": True, "trend_gate_lookback": 40,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
            "model_method": "xgb",
        }),
        ("tg_xgb_lb80_th05", {
            "trend_gate_enabled": True, "trend_gate_lookback": 80,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.0,
            "model_method": "xgb",
        }),
    ]

    # ---- Phase 3: gate factor (not just flat, but reduced exposure) ----
    phase3_variants = [
        ("tg_lb60_th05_f03", {
            "trend_gate_enabled": True, "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.3,
        }),
        ("tg_lb60_th05_f05", {
            "trend_gate_enabled": True, "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.5,
        }),
        ("tg_lb40_th05_f03", {
            "trend_gate_enabled": True, "trend_gate_lookback": 40,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.3,
        }),
        ("tg_lb40_th05_f05", {
            "trend_gate_enabled": True, "trend_gate_lookback": 40,
            "trend_gate_threshold": -0.05, "trend_gate_factor": 0.5,
        }),
    ]

    all_variants = phase1_variants + phase2_variants + phase3_variants

    import pandas as pd
    rows = []
    t_start = time.time()

    tf_cfg = d.copy()
    for i, (name, over) in enumerate(all_variants):
        merged = {}
        merged.update(tf_cfg)
        merged.update(over)
        cfg = Config(**merged)
        cfg.name = name
        cfg.out_dir = out_dir
        cfg.plot = False
        cfg.verbose = False
        SEP = "=" * 50
        print("\n" + SEP)
        print("[%d/%d] %s" % (i+1, len(all_variants), name), flush=True)
        t0 = time.time()
        try:
            res = runner.run(cfg)
            dt = time.time() - t0
            m = res.get("metrics", {})
            v = res.get("diagnostics", {}).get("verdict", {})

            # Compute honest block Sharpe
            dr_path = os.path.join(out_dir, name, "daily_returns.csv")
            rb = over.get("rebalance_freq", 20)
            bs = compute_block_sharpe(dr_path, rb) if os.path.exists(dr_path) else {}

            row = {
                "config": name,
                "sharpe": m.get("sharpe"),
                "ann_ret": m.get("annual_return"),
                "ann_vol": m.get("annual_volatility"),
                "turnover": m.get("annual_turnover"),
                "max_dd": m.get("max_drawdown"),
                "sortino": m.get("sortino"),
                "calmar": m.get("calmar"),
                "win_rate": m.get("win_rate"),
                "n_risk_events": m.get("n_risk_events"),
                "block_sharpe": bs.get("block_sharpe"),
                "n_blocks": bs.get("n_blocks"),
                "t_stat": bs.get("t_stat"),
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
            bsr = bs.get("block_sharpe", 0) or 0
            print("  Sharpe=%.4f  BlockSR=%.3f  Ret=%.1f%%  TO=%.1f  DD=%.1f%%  %s(%df)  dt=%ds" % (
                sr, bsr, ar, to, dd, v.get('assessment','?'), v.get('n_flags', 99), int(dt)), flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            rows.append({"config": name, "error": str(e), "time_s": time.time() - t0})

    df = pd.DataFrame(rows)
    csv_path = os.path.join(out_dir, "trend_gate_sweep.csv")
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_start) / 60
    print("\n" + "="*50)
    print("DONE in %.1f min. -> %s" % (dt_total, csv_path))
    print("\nTOP CONFIGS (by daily Sharpe):")
    df_ok = df[df["sharpe"].notna() & (df["sharpe"] > 0)].sort_values("sharpe", ascending=False)
    for _, r in df_ok.head(20).iterrows():
        bsr = r.get("block_sharpe", 0) or 0
        tst = r.get("t_stat", 0) or 0
        print("  %-30s DailySR=%.4f  BlockSR=%.3f  t=%.2f  Ret=%.1f%%  TO=%.1f  DD=%.1f%%  %s(%df)" % (
            r['config'], r['sharpe'], bsr, tst,
            float(r['ann_ret'])*100, r['turnover'], float(r['max_dd'])*100,
            r.get('verdict','?'), r.get('n_flags','?')))

    return 0


if __name__ == "__main__":
    sys.exit(main())
