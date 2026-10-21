#!/usr/bin/env python3
"""Regime-switching momentum + reversal strategy."""
from __future__ import annotations
import os, sys, glob
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
BIG_DIR = os.path.join(HERE, "..", "tools", "quant", "data", "twelve_big")
OUT_CSV = os.environ.get("OUT_CSV", "wf_regime_switch.csv")
START_YM = os.environ.get("START_YM", "2008-01")
COST_BPS = float(os.environ.get("COST_BPS", 6.0))
LONG_LEV = float(os.environ.get("LONG_LEV", 1.0))
VIX_LOW = float(os.environ.get("VIX_LOW", 20.0))
VIX_HIGH = float(os.environ.get("VIX_HIGH", 25.0))
GATE = int(os.environ.get("GATE", 1))
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
        except Exception: continue
    return pd.concat(all_m, axis=1).sort_index().ffill()
def main():
    import risk_gate as rg
    print("Building panel...", flush=True)
    px = build_panel()
    print(f"Panel: {px.shape[0]} months x {px.shape[1]} stocks", flush=True)
    ret1 = px.pct_change(1)
    fwd_ret = ret1.shift(-1)
    mom_sig = px.pct_change(3)
    rev_sig = -px.pct_change(2)
    vix = rg.load_daily("vix")
    vix_m = vix.resample("ME").last()
    gate_mult = None
    if GATE:
        v3 = rg.load_daily("vix3m"); s = rg.load_daily("SPY")
        gate_mult = rg.gate_multipliers(vix, v3, s, floor=0.3).shift(1)
    oos_months = [d for d in px.index if d.strftime("%Y-%m") >= START_YM]
    monthly_rets = []; one_way_turn = []; prev_w = {}
    for dt in oos_months:
        fr = fwd_ret.loc[dt]
        v = float(vix_m.asof(dt)) if pd.notna(vix_m.asof(dt)) else 20.0
        if v < VIX_LOW: w_mom, w_rev = 1.0, 0.0
        elif v >= VIX_HIGH: w_mom, w_rev = 0.0, 1.0
        else: w_mom, w_rev = 0.5, 0.5
        gv = 1.0
        if gate_mult is not None:
            gv = float(gate_mult.get(dt, 1.0)) if pd.notna(dt) else 1.0
            if pd.isna(gv): gv = 1.0
        port_ret = 0.0; w = {}
        if w_mom > 0:
            s_m = mom_sig.loc[dt].dropna()
            common = s_m.index.intersection(fr.dropna().index)
            if len(common) >= 20:
                s_m = s_m.loc[common]; fr_m = fr.loc[common]
                G = max(1, len(common)//4)
                ranked = s_m.sort_values(ascending=False)
                long_ids = ranked.index[:G]
                port_ret += w_mom * LONG_LEV * fr_m.loc[long_ids].mean()
                for s2 in long_ids: w[s2] = w.get(s2, 0) + w_mom * LONG_LEV / G
        if w_rev > 0:
            s_r = rev_sig.loc[dt].dropna()
            common = s_r.index.intersection(fr.dropna().index)
            if len(common) >= 20:
                s_r = s_r.loc[common]; fr_r = fr.loc[common]
                G = max(1, len(common)//4)
                ranked = s_r.sort_values(ascending=False)
                long_ids = ranked.index[:G]
                short_ids = ranked.index[-G:]
                port_ret += w_rev * (fr_r.loc[long_ids].mean() - fr_r.loc[short_ids].mean())
                for s2 in long_ids: w[s2] = w.get(s2, 0) + w_rev / G
                for s2 in short_ids: w[s2] = w.get(s2, 0) - w_rev / G
        port_ret *= gv
        w = {k: v*gv for k, v in w.items()}
        turnover = sum(abs(w.get(s2, 0) - prev_w.get(s2, 0)) for s2 in set(w)|set(prev_w)) / 2.0
        one_way_turn.append(turnover)
        net_ret = port_ret - turnover * COST_BPS / 10000.0
        monthly_rets.append(net_ret)
        prev_w = w
    rr = np.array(monthly_rets)
    sr = rr.mean()/(rr.std()+1e-8)*np.sqrt(12)
    ann = rr.mean()*12*100; vol = rr.std()*np.sqrt(12)*100
    eq = np.cumprod(1+rr)
    dd = min((eq[i]/max(eq[:i+1])-1) for i in range(len(eq)))*100
    print(f"\nREGIME SWITCH ({len(rr)} months) {oos_months[0].strftime(chr(37)+chr(89)+chr(45)+chr(37)+chr(109))}..{oos_months[len(rr)-1].strftime(chr(37)+chr(89)+chr(45)+chr(37)+chr(109))}")
    print(f"VIX<{VIX_LOW}: momentum, VIX>={VIX_HIGH}: reversal, gate={GATE}")
    print(f"Net: Sharpe {sr:.3f} | ann ret {ann:+.2f}% | vol {vol:.2f}% | MaxDD {dd:.2f}%")
    print(f"Turnover: {np.mean(one_way_turn)*12:.2f}x/yr")
    pd.DataFrame({"ym": [d.strftime("%Y-%m") for d in oos_months[:len(rr)]], "net": rr}).to_csv(os.path.join(HERE, "data", OUT_CSV), index=False)
if __name__ == "__main__": main()
