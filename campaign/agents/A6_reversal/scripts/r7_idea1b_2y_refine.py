"""Idea 1b: refine the 2y LF trend — cadence 42/63, k grid, 2-of-3 k-vote, tenor ensemble."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

DUR = {"2y": 1.9, "10y": 7.5, "30y": 19.0}
YLD = {"2y": "DGS2", "10y": "DGS10", "30y": "DGS30"}

def tr_series(name):
    y = L.fnew(YLD[name]) / 100.0
    tr = -DUR[name] * y.diff() + y / 252.0
    return tr.dropna()

def sig_LF(tr, k):  return (tr.rolling(k).mean() > 0).astype(float)
def sig_LS(tr, k):  return (tr.rolling(k).mean() > 0).astype(float) * 2 - 1

def ev(W, rets, tag, vt=0.12):
    r, _ = L.from_W(W, rets, vt=vt)
    rep = L.report(r, tag)
    return r, W, rets, rep

if __name__ == "__main__":
    tr2, tr10, tr30 = tr_series("2y"), tr_series("10y"), tr_series("30y")
    print("=== 2y refine ===")
    for k in [126, 189, 252, 378, 504]:
        for cad in [21, 42, 63]:
            W = L.freeze(pd.DataFrame({"d2": sig_LF(tr2, k)}), cad)
            ev(W, pd.DataFrame({"d2": tr2}), f"2yLF k{k} cad{cad}")
    # 2-of-3 k-vote
    print("--- k-vote (majority of 63/126/252 means > 0) ---")
    for cad in [21, 42]:
        v = ((sig_LF(tr2, 63) + sig_LF(tr2, 126) + sig_LF(tr2, 252)) >= 2).astype(float)
        W = L.freeze(pd.DataFrame({"d2": v}), cad)
        ev(W, pd.DataFrame({"d2": tr2}), f"2y vote63/126/252 cad{cad}")
    # tenor ensemble: equal-risk LF 2y+10y+30y at k252 (each VT-scaled by trailing own vol then summed)
    print("--- tenor ensemble LF k252, risk-parity-ish (each leg pre-scaled to 6% vol) ---")
    legs = {}
    for nm, tr in [("2y", tr2), ("10y", tr10), ("30y", tr30)]:
        s = sig_LF(tr, 252)
        sd = tr.expanding(252).std().shift(1)
        legs[nm] = s * (0.06 / np.sqrt(252) / sd).clip(0, 5).fillna(0.0)
    Lf = pd.DataFrame(legs).dropna(how="all")
    rets3 = pd.DataFrame({"2y": tr2, "10y": tr10, "30y": tr30})
    for cad in [21, 42]:
        W = L.freeze(Lf, cad)
        ev(W, rets3, f"ens(2/10/30)LF k252 cad{cad}")
    # 2y+30y two-leg
    Lf2 = pd.DataFrame({"2y": legs["2y"], "30y": legs["30y"]}).dropna(how="all")
    for cad in [21, 42]:
        W = L.freeze(Lf2, cad)
        ev(W, rets3, f"ens(2+30)LF k252 cad{cad}")
