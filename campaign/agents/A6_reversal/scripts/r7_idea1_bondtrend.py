"""Idea 1: bond rate-TREND momentum on synthetic total returns (dur approx + carry).
TR_i(d) = -D_i * dy_i + y_i/252  (par-bond approx, dec yields). Signal = trailing k-d mean TR >0 -> long.
DV01-neutral curve-neutral single-asset book, +/-1 notional (excess-return convention incl carry).
Cadence freeze (daily decision frozen to 21/5 bdays). VT 12% trailing expanding."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L
from lib6 import stats, halves_sr

DUR = {"2y": 1.9, "10y": 7.5, "30y": 19.0}
YLD = {"2y": "DGS2", "10y": "DGS10", "30y": "DGS30"}

def tr_series(name):
    y = L.fnew(YLD[name]) / 100.0
    dy = y.diff()
    tr = -DUR[name] * dy + y / 252.0
    return tr.replace([np.inf, -np.inf], np.nan).dropna()

def run(name, k, cad, short=True):
    tr = tr_series(name)
    sig = (tr.rolling(k).mean() > 0).astype(float)
    if short: sig = sig * 2 - 1          # long/short
    W = pd.DataFrame({name: sig})
    W = L.freeze(W, cad)
    rets = pd.DataFrame({name: tr})
    r, _ = L.from_W(W, rets, vt=0.12)
    return r, W, rets

if __name__ == "__main__":
    print("=== IDEA 1: bond trend (L/S and long-flat), eval 2007+, VT12, 6bps ===")
    best = None
    for name in ["10y", "2y", "30y"]:
        for k in [63, 126, 252]:
            for cad in [21, 5]:
                for short in [True, False]:
                    r, W, rets = run(name, k, cad, short)
                    rep = L.report(r, f"{name} k{k} cad{cad} {'LS' if short else 'LF'}")
                    if best is None or rep["sr"] > best[0]:
                        best = (rep["sr"], name, k, cad, short, r, W, rets, rep)
    sr, name, k, cad, short, r, W, rets, rep = best
    print(f"\nBEST: {name} k{k} cad{cad} {'LS' if short else 'LF'} SR={sr:.2f}")
    if sr >= 0.6 and rep["gates"]["c_H1>=0.3"] and rep["gates"]["c_H2>=0.3"] and rep["gates"]["d_negYr<=2"] and rep["gates"]["d_worst>-5%"] and abs(rep["c6"]) < 0.25:
        p = L.scramble(r, W, rets, vt=0.12)
        print(f"scramble p={p:.3f}")
