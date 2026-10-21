#!/usr/bin/env python3
"""Momentum 130/30 on the longer twelve_big panel (291 stocks, 2006-2026)."""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
OUT_CSV = os.environ.get("OUT_CSV", "wf_mom_long.csv")
MOM_COL = os.environ.get("MOM_LOOKBACK", "mom_3")
G_FRAC = float(os.environ.get("G_FRAC", 0.25))
LONG_LEV = float(os.environ.get("LONG_LEV", 1.0))
SHORT_LEV = float(os.environ.get("SHORT_LEV", 0.0))
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
START_YM = os.environ.get("START_YM", "2008-01")
def build_panel():
    files = sorted(glob.glob(os.path.join(BIG_DIR, "*.csv")))
    all_m = []
    for f in files:
        sym = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f, index_col=0, parse_dates=True)
            c = "close" if "close" in df.columns else df.columns[0]
            px = df[c].astype(float).dropna()
            m = px.resample("ME").last().dropna()
            m.name = sym
            all_m.append(m)
        except Exception:
            continue
    panel = pd.concat(all_m, axis=1).sort_index()
    panel = panel.ffill()
    return panel
def main():
    print("Building monthly panel from twelve_big...", flush=True)
    px = build_panel()
    print(f"Panel: {px.shape[0]} months x {px.shape[1]} stocks", flush=True)
    mom_map = {"mom_3": 3, "mom_6": 6, "mom_12": 12}
    mom_months = mom_map.get(MOM_COL, 3)
    mom = px.pct_change(mom_months)
    rets = px.pct_change(1).shift(-1)
    oos_months = [d for d in px.index if d.strftime("%Y-%m") >= START_YM]
    monthly_rets = []
    one_way_turn = []
    prev_w = {}
    # Risk gate
    gate_mult = None
    GATE = int(os.environ.get("GATE", 0))
    if GATE:
        import risk_gate as rg
        v = rg.load_daily("vix"); v3 = rg.load_daily("vix3m"); s = rg.load_daily("SPY")
        gate_mult = rg.gate_multipliers(v, v3, s, floor=0.3)
        gate_mult = gate_mult.shift(1)
        print(f"Risk gate ON: {len(gate_mult)} months", flush=True)
    for dt in oos_months:
        m = mom.loc[dt].dropna()
        r = rets.loc[dt]
        common = m.index.intersection(r.dropna().index)
        m = m.loc[common]; r = r.loc[common]
        if len(m) < 20: continue
        G = max(1, int(round(G_FRAC * len(m))))
        ranked = m.sort_values(ascending=False)
        long_ids = ranked.index[:G]
        short_ids = ranked.index[-G:]
        port_ret = LONG_LEV * r.loc[long_ids].mean()
        if SHORT_LEV > 0:
            port_ret -= SHORT_LEV * r.loc[short_ids].mean()
        # Apply risk gate
        gv = 1.0
        if gate_mult is not None:
            gv = float(gate_mult.get(dt, 1.0)) if pd.notna(dt) else 1.0
            if pd.isna(gv): gv = 1.0
            port_ret *= gv
        w = {}
        for s in long_ids: w[s] = LONG_LEV / G * gv
        for s in short_ids: w[s] = -SHORT_LEV / G * gv
        turnover = sum(abs(w.get(s, 0) - prev_w.get(s, 0)) for s in set(w) | set(prev_w)) / 2.0
        one_way_turn.append(turnover)
        net_ret = port_ret - turnover * COST_BPS / 10000.0
        monthly_rets.append(net_ret)
        prev_w = w
    rr = np.array(monthly_rets)
    sr = rr.mean() / (rr.std() + 1e-8) * np.sqrt(12)
    ann = rr.mean() * 12 * 100
    vol = rr.std() * np.sqrt(12) * 100
    eq = np.cumprod(1 + rr)
    dd = min((eq[i] / max(eq[:i+1]) - 1) for i in range(len(eq))) * 100
    print(f"MOMENTUM {MOM_COL} G={G_FRAC} L={LONG_LEV}/{SHORT_LEV} ({len(rr)} months)")
    print(f"Net: Sharpe {sr:.3f} | ann ret {ann:+.2f}% | vol {vol:.2f}% | MaxDD {dd:.2f}%")
    print(f"Turnover: {np.mean(one_way_turn)*12:.2f}x/yr")
    pd.DataFrame({"ym": [d.strftime("%Y-%m") for d in oos_months[:len(rr)]], "net": rr}).to_csv(os.path.join(HERE, "data", OUT_CSV), index=False)
if __name__ == "__main__": main()
