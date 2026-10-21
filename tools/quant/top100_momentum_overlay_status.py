"""Live status card for the top-100 momentum layered overlay (deploy config).

Deploy: monthly top-100 book + credit p85 -> flat, SPY < 200d -> flat,
VIX >= 32 -> flat, vol-target 12%, de-risked cash = 3m T-bill.
(Backtest: SR 0.890, MaxDD -12.6% vs book -50.6% — see
reports/top100_momentum_dd_overlay.md.)

Prints: data as-of dates, each gate's current value, resulting exposure for
the next trading day, and recent book vs overlay returns. Run each loop fire
to surface staleness (a gate input older than the book's last day means the
panel/FRED data needs a refresh).
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from top100_momentum_regime_filter import load_fred, exposure_pct
from top100_momentum_dd_overlay import gate_from_bool, overlay

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats/data_fred")
EQ_PATH = os.path.join(ROOT, "tools/quant/reports/top100_momentum_eq.csv")
SPY_PATH = os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv")


def main():
    eq = pd.read_csv(EQ_PATH, parse_dates=["date"]).set_index("date")
    r = eq["strategy_ret"].dropna()
    idx = r.index

    spy = pd.read_csv(SPY_PATH, parse_dates=["date"]).set_index("date")["close"]
    spy = spy.sort_index()
    vix = load_fred("vix.csv")
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()
    tb = (load_fred("tbill3m.csv") / 100.0 / 252.0)

    # --- gate inputs (latest available) ---
    spy_a = spy.reindex(idx).ffill()
    sma200 = spy_a.rolling(200).mean()
    spread_pct = spread.rolling(252, min_periods=252).rank(pct=True)
    v20 = r.tail(20).std() * np.sqrt(252)

    # --- exposure series (lagged 1d inside builders) ---
    gates = [
        exposure_pct(spread, idx, 0.85, 0.0),
        gate_from_bool(spy_a > sma200, 0.0, idx),
        gate_from_bool(vix < 32, 0.0, idx),
    ]
    cash = tb.reindex(idx).ffill().fillna(0.0)
    ov_r, exp = overlay(r, gates, cash, vol_target=0.12)
    cur = exp.iloc[-1]

    print("=" * 68)
    print("TOP-100 MOMENTUM OVERLAY — live status (deploy: credit+trend+vix+vt12)")
    print("=" * 68)
    print(f"  book data through   : {r.index.max().date()}   ({len(r)} days)")
    print(f"  SPY as-of           : {spy.index.max().date()}")
    print(f"  VIX as-of           : {vix.index.max().date()}")
    print(f"  BAA/AAA as-of       : {spread.index.max().date()}")
    print("-" * 68)
    s_now = spread.iloc[-1]
    print(f"  credit gate: BAA-AAA {s_now:.2f}% | trailing pct "
          f"{spread_pct.reindex(idx).ffill().iloc[-1]:.2f} | gate "
          f"{'FLAT' if gates[0].iloc[-1] < 0.5 else 'open'} (flat >= p85)")
    print(f"  trend gate : SPY {spy_a.iloc[-1]:.2f} vs 200d SMA {sma200.iloc[-1]:.2f}"
          f" | {'FLAT' if gates[1].iloc[-1] < 0.5 else 'open'}")
    print(f"  vix stop   : VIX {vix.iloc[-1]:.2f} | "
          f"{'FLAT' if gates[2].iloc[-1] < 0.5 else 'open'} (flat >= 32)")
    print(f"  vol target : book 20d vol {v20:.1%} | scale {min(1.0, 0.12 / v20):.2f}"
          f" (target 12%)")
    stance = "FLAT" if cur < 1e-9 else ("FULL" if cur > 0.99 else "PARTIAL")
    print("-" * 68)
    print(f"  CURRENT EXPOSURE : {cur:6.1%}   -> stance {stance}")
    print("-" * 68)
    last10 = r.tail(10)
    ov10 = ov_r.tail(10)
    print(f"  last 10 sessions : book {(1 + last10).prod() - 1:+.2%} | "
          f"overlay {(1 + ov10).prod() - 1:+.2%}")
    eq_c = (1 + r).cumprod()
    dd_now = eq_c.iloc[-1] / eq_c.cummax().iloc[-1] - 1
    ov_eq = (1 + ov_r).cumprod()
    ov_dd = ov_eq.iloc[-1] / ov_eq.cummax().iloc[-1] - 1
    print(f"  current drawdown : book {dd_now:+.2%} | overlay {ov_dd:+.2%}")
    print("=" * 68)


if __name__ == "__main__":
    main()
