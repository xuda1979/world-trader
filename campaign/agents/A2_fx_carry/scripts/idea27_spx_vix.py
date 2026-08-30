"""Charter 2: SPX + VIX-regime momentum. Long SPY when VIX<25 (VIX lagged 1d for pub honesty),
flat above. Vol budget 20% (documented). Sweep threshold 20/22/25/28 + optional trend gate."""
import sys; sys.path.insert(0, __file__.rsplit("/",1)[0])
from r4_lib import *
from data import panel

SPY = panel()["SPY"]["close"].dropna()
VIX = px_fred("vix")

def vix_regime(thr, lag=1, trend=None):
    reg = (VIX.shift(lag) < thr).astype(float)
    pos = reg.reindex(SPY.index).ffill().fillna(0.0)
    if trend:
        mom = SPY / SPY.shift(trend) - 1.0
        pos = pos * (mom > 0).astype(float).fillna(0.0)
    return pos

for thr in (20, 22, 25, 28):
    for lag in (1, 2):
        net, netvt = run_mech(vix_regime(thr, lag), SPY, 0.20)
        g = full_gates(netvt); c, n = corr_to_champ(netvt)
        pr(f"SPY-VIX<{thr}-lag{lag}-vt20", g, c, f"n={n}")
# + trend gate variants at best thresholds
for thr in (22, 25):
    for tw in (126, 252):
        net, netvt = run_mech(vix_regime(thr, 1, tw), SPY, 0.20)
        g = full_gates(netvt); c, n = corr_to_champ(netvt)
        pr(f"SPY-VIX<{thr}-tr{tw}-vt20", g, c, f"n={n}")
