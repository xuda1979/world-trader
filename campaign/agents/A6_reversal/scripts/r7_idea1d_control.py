"""Idea 1d: controls — always-long 2y TR (pure term premium), and k-grid edge robustness."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
import r7_lib as L

def tr2y():
    y = L.fnew("DGS2") / 100.0
    return (-1.9 * y.diff() + y / 252.0).dropna()

tr = tr2y()
# control 1: always long
W = pd.DataFrame({"d2": np.ones(len(tr))}, index=tr.index)
r, _ = L.from_W(W, pd.DataFrame({"d2": tr}), vt=0.12)
L.report(r, "CONTROL always-long 2y")
# control 2: always long, VT capped at 1 (no leverage, pure beta)
r2, lev = L.from_W(W, pd.DataFrame({"d2": tr}), vt=0.12, cap=1.0)
L.report(r2, "CONTROL always-long 2y cap1 (no lev)")
# control 3: long when trailing 1y carry estimate>0 (y/252*63 always>0 -> always long; skip)
# what does the trend filter avoid? yearly of raw TR long-only unlevered:
yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
print("always-long VT12 yearly:", {int(k): round(v*100,1) for k,v in yr.items()})
W3, rets = pd.DataFrame({"d2": (tr.rolling(378).mean() > 0).astype(float)}), pd.DataFrame({"d2": tr})
W3 = L.freeze(W3, 42)
r3, _ = L.from_W(W3, rets, vt=0.12)
yr3 = r3.groupby(r3.index.year).apply(lambda x: (1+x).prod()-1)
print("trend VT12 yearly:      ", {int(k): round(v*100,1) for k,v in yr3.items()})
# flat periods (when filter was OUT)
out = W3["d2"][W3["d2"]==0]
def spans(idx):
    if len(idx)==0: return []
    sp=[]; s=idx[0]; p=idx[0]
    for d in idx[1:]:
        if (d-p).days>10: sp.append((s.date(),p.date())); s=d
        p=d
    sp.append((s.date(),p.date())); return sp
print("flat spans:", spans(out.index))
