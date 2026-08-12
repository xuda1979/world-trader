"""Depth-3 CAPM-alpha + Trend Gate combination test (2026-08-04).

champ_d3_mkt_bw120 (GBRT d=3, CAPM-alpha ff3_real mkt bw120, NO trend gate)
gets daily Sharpe 2.316, block Sharpe 1.77 (t=2.49), turnover 3.4.

The trend gate champion (GBRT d=2, demean, trend gate flat60) gets
daily Sharpe 2.269, block Sharpe 1.95 (t=2.74), turnover 5.04.

This test combines BOTH improvements: d=3 + CAPM-alpha label + trend gate.
If additive, expected daily Sharpe > 2.4, block Sharpe > 2.0.
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls import runner


RESULTS = os.path.join(os.path.dirname(__file__), "results")
SRC_CFG = os.path.join(ROOT, "tools/quant/ls/results/iter2_probes/champ_d3_mkt_bw120.config.json")


def compute_block_sharpe(daily_csv_path, rebalance_freq):
    import pandas as pd
    import numpy as np
    df = pd.read_csv(daily_csv_path, index_col=0)
    r = df['daily_return'].values
    n = len(r)
    blocks = []
    for i in range(0, n, rebalance_freq):
        b = r[i:min(i+rebalance_freq,n)]
        if len(b) >= max(3, rebalance_freq//2):
            blocks.append((1+b).prod()-1)
    if len(blocks) < 5:
        return {"block_sharpe": np.nan, "n_blocks": len(blocks), "t_stat": np.nan}
    arr = np.array(blocks)
    mu, sd = arr.mean(), arr.std(ddof=1)
    if sd == 0:
        return {"block_sharpe": np.nan, "n_blocks": len(arr), "t_stat": np.nan}
    ann_sr = (mu/sd)*np.sqrt(252/rebalance_freq)
    t_stat = mu/(sd/np.sqrt(len(arr)))
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

    out_dir = os.path.join(RESULTS, "d3_tg_test")
    os.makedirs(out_dir, exist_ok=True)

    variants = [
        ("d3_no_gate", {
            "trend_gate_enabled": False,
        }),
        ("d3_tg_flat60", {
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        ("d3_tg_flat40", {
            "trend_gate_enabled": True,
            "trend_gate_lookback": 40,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
        }),
        ("d3_tg_half60", {
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.5,
        }),
        ("d3_tg_flat60_th07", {
            "trend_gate_enabled": True,
            "trend_gate_lookback": 60,
            "trend_gate_threshold": -0.07,
            "trend_gate_factor": 0.0,
        }),
        ("d3_tg_flat80", {
            "trend_gate_enabled": True,
            "trend_gate_lookback": 80,
            "trend_gate_threshold": -0.05,
            "trend_gate_factor": 0.0,
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
        print("\n" + "="*50)
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
                "config": name, "sharpe": m.get("sharpe"),
                "ann_ret": m.get("annual_return"), "ann_vol": m.get("annual_volatility"),
                "turnover": m.get("annual_turnover"), "max_dd": m.get("max_drawdown"),
                "block_sharpe": bs.get("block_sharpe"), "n_blocks": bs.get("n_blocks"),
                "t_stat": bs.get("t_stat"), "verdict": v.get("assessment"),
                "n_flags": v.get("n_flags"),
                "flags": "; ".join(v.get("overfitting_flags", [])), "time_s": dt,
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
    csv_path = os.path.join(out_dir, "d3_tg_results.csv")
    df.to_csv(csv_path, index=False)
    dt_total = (time.time() - t_start) / 60
    print("\nDONE in %.1f min. -> %s" % (dt_total, csv_path))
    df_ok = df[df["sharpe"].notna() & (df["sharpe"] > 0)].sort_values("sharpe", ascending=False)
    for _, r in df_ok.iterrows():
        print("  %-25s DaySR=%.4f  BlockSR=%.3f  t=%.2f  Ret=%.1f%%  TO=%.1f  %s(%df)" % (
            r['config'], r['sharpe'], r.get('block_sharpe',0) or 0, r.get('t_stat',0) or 0,
            float(r['ann_ret'])*100, r['turnover'], r.get('verdict','?'), r.get('n_flags','?')))
    return 0

if __name__ == "__main__":
    sys.exit(main())
