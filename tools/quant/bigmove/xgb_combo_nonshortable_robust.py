"""Robustness of the non-shortable (short-liquidity) constraint at p=30%.

Manager directive (2026-08-24 standup, Agent B): confirm the SR lift from
restricting the short leg to liquid/borrowable names (p=30%) is NOT a
p-sampling artifact -- sweep MR-sleeve variant and vol-target at fixed p, with
1% blended borrow, contrasting p=0 (baseline) vs p=0.30.

Cells: MR in {k5_n20, k3_n30, k5_n30, k5_n40} x VT target in {0.12, 0.14, 0.16}.
Short-restriction imports load_1y_ex1st_monthly / load_1m_monthly from
xgb_combo_nonshortable (they take p). MR backtest is re-run per (k,n).
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import xgb_combo_nonshortable as NS   # reuses load_1y_ex1st_monthly / load_1m_monthly
ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
COST = 0.0006
W1Y = 0.75
VT_CAP = 1.5
DXY_Z, DXY_F = 1.5, 0.5
CR_WIN, CR_THR, CR_F2 = 12, 1.3, 0.5
MR_MC = 1.0
MR_F = 0.4
BORROW_RATE = 0.01
MR_VARIANTS = [(5, 20), (3, 30), (5, 30), (5, 40)]
VT_TARGETS = [0.12, 0.14, 0.16]


def stats_monthly(s):
    s = s.dropna()
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4)}


def run_cell(legs, mr_dict, vt_tgt, vt_win):
    combo = W1Y * legs["y1"] + (1 - W1Y) * legs["m1"]
    mr = mr_dict.reindex(combo.index).dropna()
    al = pd.concat([combo.rename("combo"), mr.rename("mr")], axis=1).dropna()
    combo, mr = al["combo"], al["mr"]
    rv = combo.rolling(vt_win, min_periods=vt_win - 3).std() * np.sqrt(12)
    sc_vt = (vt_tgt / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
    dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    dm = dxy.rolling(12, min_periods=8).mean(); dsd = dxy.rolling(12, min_periods=8).std()
    dFLAG = (((dxy - dm) / dsd).reindex(combo.index).ffill().shift(1) > DXY_Z).fillna(False)
    dgate = pd.Series(1.0, index=combo.index); dgate[dFLAG] = DXY_F
    aaa = pd.read_csv(os.path.join(FRED, "aaa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    baa = pd.read_csv(os.path.join(FRED, "baa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    cs = (baa - aaa)
    cz = (cs - cs.rolling(CR_WIN, min_periods=8).mean()) / cs.rolling(CR_WIN, min_periods=8).std()
    cFLAG = (cz.reindex(combo.index).ffill().shift(1) > CR_THR).fillna(False)
    fac = sc_vt * dgate
    fac[cFLAG] *= CR_F2
    champ = combo * fac - fac.diff().abs().fillna(0.0) * 2 * COST
    uFLAG = (dFLAG | cFLAG)
    base = champ + mr * MR_MC * MR_F * uFLAG.astype(float)
    borrow = (fac + MR_F * uFLAG.astype(float)) * BORROW_RATE / 12.0
    return champ, base - borrow


def main():
    # pre-build legs once per p (MR variants share the same legs)
    print("building legs p=0 and p=0.30...", flush=True)
    legs0 = pd.concat([NS.load_1y_ex1st_monthly(0.0).rename("y1"),
                       NS.load_1m_monthly(0.0).rename("m1")], axis=1).dropna()
    legs0 = legs0[legs0.index >= "2009-01-01"]
    legs30 = pd.concat([NS.load_1y_ex1st_monthly(0.30).rename("y1"),
                        NS.load_1m_monthly(0.30).rename("m1")], axis=1).dropna()
    legs30 = legs30[legs30.index >= "2009-01-01"]

    # MR monthly per variant
    sys.path.insert(0, ROOT)
    from tools.quant.hedge_fund_strats.meanrev_episode_research import load_prices_rets, backtest
    prices, rets = load_prices_rets()
    mr_variants = {}
    for (k, n) in MR_VARIANTS:
        d = backtest(prices, rets, k, n)
        m = d.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        m.index = pd.to_datetime(m.index)
        mr_variants[(k, n)] = m

    print(f"\n=== p=0 (baseline) vs p=0.30, x MR variant x VT target, +1% borrow ===")
    rows = []
    for (k, n), mrs in mr_variants.items():
        for vt in VT_TARGETS:
            _, b0 = run_cell(legs0, mrs, vt, 12)
            _, b30 = run_cell(legs30, mrs, vt, 12)
            s0, s30 = stats_monthly(b0), stats_monthly(b30)
            rows.append({"mr": f"k{k}_n{n}", "vt": vt, "sr0": s0["sr"], "sr30": s30["sr"],
                         "d_sr": round(s30["sr"] - s0["sr"], 3),
                         "ann0": s0["ann"], "ann30": s30["ann"],
                         "dd0": s0["dd"], "dd30": s30["dd"]})
            print(f"  k{k}_n{n} VT{vt}: SR {s0['sr']}->{s30['sr']} (Δ{rows[-1]['d_sr']:+.3f}) "
                  f"ann {s0['ann']:+.1%}->{s30['ann']:+.1%} dd {s0['dd']:+.1%}->{s30['dd']:+.1%}")

    ds = [r["d_sr"] for r in rows]
    print(f"\nSummary: p=0.30 vs p=0 ΔSR mean {np.mean(ds):+.3f}, min {min(ds):+.3f}, "
          f"max {max(ds):+.3f}; positive in {(np.array(ds) > 0).mean():.0%} of cells")
    json.dump({"cells": rows, "borrow_rate": BORROW_RATE, "p30": 0.30, "p0": 0.0,
               "summary": {"d_sr_mean": round(float(np.mean(ds)), 3),
                           "d_sr_min": round(float(min(ds)), 3),
                           "d_sr_max": round(float(max(ds)), 3),
                           "frac_positive": float((np.array(ds) > 0).mean())}},
              open(os.path.join(OUT, "xgb_combo_nonshortable_robust.json"), "w"), indent=2, default=str)


if __name__ == "__main__":
    main()
