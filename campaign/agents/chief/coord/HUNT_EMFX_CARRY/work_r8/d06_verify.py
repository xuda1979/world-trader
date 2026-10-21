import os, sys
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import emfx_lib as L
CH = L.champion(); PX = L.panel(); CARRY = L.carry_brl(CH.index)
PU = L.total_perunit(PX, CARRY).fillna(0.0); AVAIL = PX.notna()
LR = np.log(PX)
def zsign(x): return np.sign(x.fillna(0.0))
mom252 = LR - LR.shift(252)
S = {}
S["C3_TSMOM_252"] = zsign(mom252)
S["C5_BRL_MOM_252"] = pd.DataFrame({"BRL": zsign(mom252["BRL"])}, index=CH.index)
S["C1_BRL_CARRY_L"] = pd.DataFrame({"BRL": np.where(CARRY > 0, 1.0, 0.0)}, index=CH.index)
mx = 0.0
for k, sig in S.items():
    sig = sig.where(AVAIL, 0.0).fillna(0.0)
    w = L.effective_weights(sig, PU, target=0.10)
    g = w.abs().sum(axis=1); mx = max(mx, float(g.max()))
    tail = w["PLN"].loc["2026-01-01":] if "PLN" in w.columns else None
    if tail is None:
        print("%-18s max_gross=%.6f gross_ok=%s (BRL-only book)" % (k, g.max(), bool(g.max() <= 1.6))); continue
    print("%-18s max_gross=%.6f  gross_ok=%s  PLN_post2025 max|w|=%.8f n_nonzero=%d" % (
        k, g.max(), bool(g.max() <= 1.6), tail.abs().max(), int((tail.abs() > 0).sum())))
print("\nglobal max gross over sampled candidates: %.6f -> gross<=1.6 %s" % (
    mx, "HELD" if mx <= 1.6 else "VIOLATED"))
sig = S["C3_TSMOM_252"].where(AVAIL, 0.0).fillna(0.0)
w = L.effective_weights(sig, PU, target=0.10)
print("C3 final-day weights 2026-08-28:", dict((c, round(float(w[c].iloc[-1]), 4)) for c in L.CCY))
print("C3 max gross overall: %.6f" % w.abs().sum(axis=1).max())
