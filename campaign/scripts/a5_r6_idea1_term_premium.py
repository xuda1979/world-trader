"""A5 r6 idea1 (charter): term-premium timing. Long 10y synth TR (dur 7.5) only when
t10y2y slope > 0 AND us10y < its 252d mean, monthly cadence. T+1, 6bps, vt10.
Gates r6: SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05, plateau."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import data as D
from a5_r6_lib import build_net, gates_r6, corr_table

y10, y2 = D.fred("us10y"), D.fred("us2y")
Y = pd.DataFrame({"y": y10, "y2": y2}).dropna()
Y = Y[Y.index >= "2000-01-01"]
slope = Y["y"] - Y["y2"]                       # identical to FRED t10y2y (verified corr 1.0)
dy = Y["y"].diff() / 100.0
carry = Y["y"].ffill() / 100.0 / 252.0
TR = 7.5 * (-dy) + carry                       # synth 10y TR, dur 7.5
R = TR.reindex(Y.index)

def build(ma=252, cadence="monthly", slope_on=True, dur=7.5):
    slopeok = (slope > 0).astype(float) if slope_on else pd.Series(1.0, index=Y.index)
    valueok = (Y["y"] < Y["y"].rolling(ma).mean()).astype(float)
    sig = valueok * slopeok
    if cadence == "monthly":
        ms = sig.groupby([sig.index.year, sig.index.month]).tail(1).index
        sig = sig.loc[ms].reindex(sig.index).ffill()
    elif cadence == "weekly":
        ws = sig.groupby(pd.Grouper(freq="W-FRI")).tail(1).index
        sig = sig.loc[ws].reindex(sig.index).ffill()
    return sig

rows = []
for ma in (126, 252, 504):
    for cad in ("daily", "weekly", "monthly"):
        for so in (True, False):
            sig = build(ma, cad, so)
            net, posf = build_net(sig, R, vt=0.10)
            ok, line = gates_r6(f"tp ma{ma} {cad} slope{int(so)}", net, posf, R)
            rows.append((ok["a"] and ok["c"] and ok["d"] and ok["e"], srm := net.resample("ME").apply(lambda x:(1+x).prod()-1), line))
            print(line)
best = max((np.sqrt(252)*r_.mean()/r_.std() if r_.std()>0 else 0, l) for ok, r_, l in rows)
print("BEST SR_m:", round(best[0],2), "|", best[1])
