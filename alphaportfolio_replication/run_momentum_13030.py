#!/usr/bin/env python3
"""Momentum 130/30 walk-forward harness with realistic IB financing.

The REAL champion: simple momentum 130/30 on S&P 500.
  - Top G stocks by MOM_LOOKBACK momentum: 130% long (equal-weight)
  - Bottom G stocks: 30% short (equal-weight)  
  - Monthly rebalance
  - 6bps one-side turnover cost
  - IB-level short financing: (call_rate - 1.5% rebate + 0.25% fee) on short MV
  - Optional VIX/drawdown risk gate (risk_gate.py)

Free data: S&P 500 monthly panel (data/model_panel_full.csv).
Walk-forward: the full panel IS the OOS (no training needed — momentum
is parameter-free, so there's no model to retrain. The "retrain" = monthly
rebalance, always fresh by construction).

Usage:
  python run_momentum_13030.py
  env MOM_LOOKBACK=12 G_FRAC=0.25 LONG_LEV=1.3 SHORT_LEV=0.3 GATE=1 ...
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

PANEL = os.path.join(HERE, "data", "model_panel_full.csv")
OUT_CSV = os.environ.get("OUT_CSV", "wf_mom13030.csv")

# Strategy params
MOM_LOOKBACK = os.environ.get("MOM_LOOKBACK", "mom_12_1")  # which momentum feature
G_FRAC = float(os.environ.get("G_FRAC", 0.25))   # fraction of universe per side
LONG_LEV = float(os.environ.get("LONG_LEV", 1.3))
SHORT_LEV = float(os.environ.get("SHORT_LEV", 0.3))
START_YM = os.environ.get("START_YM", "2021-09")

# Costs
COST_BPS = float(os.environ.get("COST_BPS", 6.0))  # one-side turnover
SHORT_BORROW = int(os.environ.get("SHORT_BORROW", 1))
SHORT_REBATE_BPS = float(os.environ.get("SHORT_REBATE_PAID_BPS", 150.0))
SHORT_FEE_BPS = float(os.environ.get("SHORT_BORROW_FEE_BPS", 25.0))

# Risk gate
GATE = int(os.environ.get("GATE", 0))  # 1 = apply VIX/drawdown gate


def load_call_rate():
    p = os.path.join(HERE, "data", "irx_daily.csv")
    if os.path.exists(p):
        cr = pd.read_csv(p, parse_dates=["DATE"], index_col="DATE")
        return cr["call_rate"].astype(float)
    return None


def main():
    panel = pd.read_csv(PANEL)
    panel["ret1_frac"] = panel["ret1"] / 100.0  # convert % to fraction
    all_ym = sorted(panel["ym"].unique().tolist())

    call_rate = load_call_rate() if SHORT_BORROW else None

    # Load risk gate
    gate_mult = None
    if GATE:
        import risk_gate as rg
        v = rg.load_daily("vix"); v3 = rg.load_daily("vix3m"); s = rg.load_daily("SPY")
        gate_mult = rg.gate_multipliers(v, v3, s, floor=0.3)
        gate_mult = gate_mult.shift(1)  # signal from month t-1 -> positions in month t
        print(f"Risk gate ON: {len(gate_mult)} months", flush=True)

    oos_ym = [m for m in all_ym if m >= START_YM]
    monthly_rets = []
    one_way_turn = []
    short_fin_costs = []
    prev_w = {}

    for ym in oos_ym:
        grp = panel[panel["ym"] == ym].dropna(subset=[MOM_LOOKBACK, "ret1_frac"])
        n = len(grp)
        if n < 20:
            monthly_rets.append(0.0)
            one_way_turn.append(0.0)
            short_fin_costs.append(0.0)
            continue

        G = max(1, int(round(G_FRAC * n)))
        ranked = grp.sort_values(MOM_LOOKBACK, ascending=False)
        long_ids = ranked.index[:G].tolist()
        short_ids = ranked.index[-G:].tolist()

        # Equal-weight 130/30
        w = {}
        for i in long_ids:
            w[grp.loc[i, "symbol"]] = LONG_LEV / G
        for i in short_ids:
            w[grp.loc[i, "symbol"]] = -SHORT_LEV / G

        # Apply risk gate
        if gate_mult is not None:
            ts = pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(0)
            gv = float(gate_mult.get(ts, 1.0)) if pd.notna(ts) else 1.0
            if pd.isna(gv): gv = 1.0
            w = {k: v * gv for k, v in w.items()}

        # Portfolio return
        port_ret = 0.0
        for i in long_ids:
            port_ret += (LONG_LEV / G) * grp.loc[i, "ret1_frac"]
        for i in short_ids:
            port_ret += -(SHORT_LEV / G) * grp.loc[i, "ret1_frac"]

        # Turnover (one-way)
        common_syms = set(w) | set(prev_w)
        turnover = sum(abs(w.get(s, 0) - prev_w.get(s, 0)) for s in common_syms) / 2.0
        one_way_turn.append(turnover)

        # Short financing cost
        if SHORT_BORROW and call_rate is not None:
            ts = pd.Timestamp(ym + "-01") + pd.offsets.MonthEnd(0)
            cr = float(call_rate.asof(ts)) if pd.notna(call_rate.asof(ts)) else 5.0
            net_short_pct = (cr - SHORT_REBATE_BPS/100 + SHORT_FEE_BPS/100) / 100.0
            short_mv = SHORT_LEV * (gv if gate_mult is not None else 1.0)
            sf = (net_short_pct / 12.0) * short_mv
        else:
            sf = 0.0
        short_fin_costs.append(sf)

        # Net return
        turn_cost = turnover * COST_BPS / 10000.0
        net_ret = port_ret - turn_cost - sf
        monthly_rets.append(net_ret)
        prev_w = w

    # Results
    r = np.array(monthly_rets)
    sr = r.mean() / (r.std() + 1e-8) * np.sqrt(12)
    ann_ret = r.mean() * 12 * 100
    ann_vol = r.std() * np.sqrt(12) * 100
    eq = np.cumprod(1 + r)
    dd = min((eq[i] / max(eq[:i+1]) - 1) for i in range(len(eq))) * 100
    ann_turn = np.mean(one_way_turn) * 12
    cost_drag = (np.mean(one_way_turn) * COST_BPS / 10000.0 + np.mean(short_fin_costs)) * 12 * 100

    print(f"\n{'='*70}")
    print(f"MOMENTUM 130/30 WALK-FORWARD ({len(oos_ym)} months) {oos_ym[0]}..{oos_ym[-1]}")
    print(f"  mom={MOM_LOOKBACK} G={G_FRAC} L={LONG_LEV}/{SHORT_LEV} gate={GATE}")
    print(f"  cost={COST_BPS}bps + IB short financing")
    print(f"{'='*70}")
    print(f"Net:  Sharpe {sr:.3f} | ann ret {ann_ret:+.2f}% | ann vol {ann_vol:.2f}% | MaxDD {dd:.2f}%")
    print(f"Annualized turnover: {ann_turn:.2f}x | Cost drag: {cost_drag:.3f}%/yr")

    pd.DataFrame({"ym": oos_ym, "net": r}).to_csv(
        os.path.join(HERE, "data", OUT_CSV), index=False)
    return sr


if __name__ == "__main__":
    main()
