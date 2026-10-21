"""CANDIDATE live signal on the POLYGON champion (n10_r14) — READY, NOT SWITCHED.

The twelvedata live config FAILS on the current extended panel (SR -0.19
on 20y, +0.03 on 8y — see RESEARCH_LOG 2026-08-12). The ls framework's
LIVE RECOMMENDATION: migrate to the polygon champion (n10_r14, SR 1.42,
scramble PASS, polygon data only). This is the migration candidate,
prepared non-destructively; run_live_signal.py is NOT switched until the
user decides (the ls framework marked it "user decision").

Usage: python -m tools.quant.ls.run_live_signal_polygon
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from tools.quant.ls.config import Config
from tools.quant.ls import runner
from tools.quant.ls.run_live_signal import check_screen_state

OUT_JSON = os.path.join(ROOT, "tools/quant/ls/results/live_signal_polygon.json")

# n10_r14 polygon champion config (from regime_gbrt_v13_oos.py, polygon panel)
def main() -> int:
    cfg = Config(
        data_dir="tools/quant/data/polygon",
        use_macro=True,
        model_method="gbrt",
        train_window=160,
        refit_freq=20,
        rebalance_freq=14,
        predict_horizon=10,
        return_horizon_fwd=10,
        n_long=10,
        n_short=10,
        vol_target_active=False,
        gross_leverage=1.0,
        cost_bps_one_side=6.0,
        slippage_bps=0.0,
        vix_derisk_factor=1.0,
        vix_level_threshold=32.0,
        vix_level_factor=0.3,
        use_call_rate_financing=True,
        long_financing_apply=True,
    ).set(name="live_signal_polygon", plot=False, verbose=False)
    print("Running polygon champion (n10_r14) live pipeline...", flush=True)
    res = runner.run(cfg)
    m = res.get("metrics", {})
    result = res.get("result") or {}
    holdings = result.get("holdings")
    if holdings is None or holdings.empty:
        print("No holdings available.")
        return 1
    last_date = holdings.index[-1]
    w = holdings.iloc[-1]
    longs = w[w > 0].sort_values(ascending=False)
    shorts = w[w < 0].sort_values()
    signal = {
        "as_of": str(last_date.date()),
        "config": "polygon champion n10_r14 (migration candidate)",
        "gross_exposure": float(holdings.iloc[-1].abs().sum()),
        "net_exposure": float(holdings.iloc[-1].sum()),
        "avg_abs_beta": m.get("avg_abs_beta"),
        "annualized_sharpe_daily_returns": m.get("sharpe"),
        "annualized_return": m.get("annual_return"),
        "max_drawdown": m.get("max_drawdown"),
        "longs": [{"ticker": t, "weight": round(float(weight), 4)} for t, weight in longs.items()],
        "shorts": [{"ticker": t, "weight": round(float(weight), 4)} for t, weight in shorts.items()],
    }
    with open(OUT_JSON, "w") as f:
        json.dump(signal, f, indent=2)
    print(f"=== CANDIDATE LIVE SIGNAL — polygon champion n10_r14 (as of {signal['as_of']}) ===")
    print(f"Gross {signal['gross_exposure']:.2f} | Net {signal['net_exposure']:.3f} | "
          f"beta {signal['avg_abs_beta']:.3f}")
    print(f"Backtest: SR {signal['annualized_sharpe_daily_returns']:.3f} | "
          f"ret {signal['annualized_return']*100:.1f}% | DD {signal['max_drawdown']*100:.1f}%")
    print("LONG :", ", ".join(f"{x['ticker']} {x['weight']:+.3f}" for x in signal["longs"]))
    print("SHORT:", ", ".join(f"{x['ticker']} {x['weight']:+.3f}" for x in signal["shorts"]))
    print(f"\nSaved -> {OUT_JSON} (NOT wired into live automation; user decision pending)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
