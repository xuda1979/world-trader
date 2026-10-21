"""V2 Factors + Trend Gate combination test (2026-08-04).

Tests the 15 academic alpha factors (factors_v2.py) combined with the
trend gate on the champion config (rb20_tw160, GBRT d=2, 3.8bps).

Variants:
  v2_baseline      — V2 factors ON, trend gate OFF, bypass_ic_screen (GBRT does feature selection)
  v2_icir08        — V2 factors ON, ICIR screen at 0.08 threshold
  v2_icir10        — V2 factors ON, ICIR screen at 0.10 threshold (relaxed)
  v2_tg_flat60     — V2 factors + trend gate (lb=60, th=-0.05, flat)
  v2_tg_flat40     — V2 factors + trend gate (lb=40, th=-0.05, flat)
  v2_tg_flat60_ic  — V2 factors + trend gate + ICIR screen
  v2_tg_flat40_ic  — V2 factors + trend gate + ICIR screen
  v2_xgb_flat60    — V2 factors + XGBoost + trend gate
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

    out_dir = os.path.join(RESULTS, "v2_trend_gate_test")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        # V2 factors alone (bypass ICIR so GBRT sees all ~15+ new factors)
        ("v2_baseline", {
            "use_v2_factors": True,
            "bypass_ic_screen": True,
            "trend_gate_enabled": False,
        }),
        # V2 factors with relaxed ICIR screen
        ("v2_icir10", {
            "use_v2_factors": True,
            "bypass_ic_screen": False,
            "icir_threshold": 0.10,
            "ic_mean_threshold": 0.005,
            "ic_bonferroni": False,
            "trend_gate_enabled": False,
        }),
        ("v2_icir08", {
            "use_v2_factors": True,
            "bypass_ic_screen": False,
            "icir_threshold": 0.08,
            "ic_mean_threshold": 0.005,
            "ic_bonferroni": False,
            "trend_gate_enabled": False,
        }),
        # V2 factors + trend gate (go flat in bear)
        ("v2_tg_flat60", {
            "use_v2_factors": True,
            "bypass_ic_screen": True,
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        ("v2_tg_flat40", {
            "use_v2_factors": True,
            "bypass_ic_screen": True,
            "trend_gate_enabled": True,
            "trend_gate_lookback": 40,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        # V2 factors + ICIR + trend gate
        ("v2_icir10_tg60", {
            "use_v2_factors": True,
            "bypass_ic_screen": False,
            "icir_threshold": 0.10,
            "ic_mean_threshold": 0.005,
            "ic_bonferroni": False,
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        # XGBoost + V2 factors + trend gate
        ("v2_xgb_tg60", {
            "use_v2_factors": True,
            "bypass_ic_screen": True,
            "model_method": "xgb",
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        # XGBoost + V2 factors (no gate, baseline)
        ("v2_xgb", {
            "use_v2_factors": True,
            "bypass_ic_screen": True,
            "model_method": "xgb",
            "trend_gate_enabled": False,
        }),
    ]

    import pandas as pd
    rows = []
    t_start = time.time()

    tf_cfg = d.copy()
    for i, (name, over) in enumerate(variants):
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
        print("[%d/%d] %s" % (i+1, len(variants), name), flush=True)
        t0 = time.time()
        try:
            res = runner.run(cfg)
            dt = time.time() - t0
            m = res.get("metrics", {})
            v = res.get("diagnostics", {}).get("verdict", {})

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
    csv_path = os.path.join(out_dir, "v2_trend_gate_test.csv")
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_start) / 60
    print("\n" + "="*50)
    print("DONE in %.1f min. -> %s" % (dt_total, csv_path))
    print("\nRESULTS (by daily Sharpe):")
    df_ok = df[df["sharpe"].notna() & (df["sharpe"] > 0)].sort_values("sharpe", ascending=False)
    for _, r in df_ok.iterrows():
        bsr = r.get("block_sharpe", 0) or 0
        tst = r.get("t_stat", 0) or 0
        print("  %-25s DailySR=%.4f  BlockSR=%.3f  t=%.2f  Ret=%.1f%%  TO=%.1f  DD=%.1f%%  %s(%df)" % (
            r['config'], r['sharpe'], bsr, tst,
            float(r['ann_ret'])*100, r['turnover'], float(r['max_dd'])*100,
            r.get('verdict','?'), r.get('n_flags','?')))
    return 0


if __name__ == "__main__":
    sys.exit(main())
