"""C1 idea 1: cross-sectional industry momentum, 48 KF industries VW (2008+, T+1, 6bps).
Also contains idea 2 (reversal) via sgn=-1. Full grid incl. skip and hold.
Run: python3 campaign/scripts/c1_idea1_indmom.py"""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.scripts.c1_lib import kf48, bt, vt, stats, gates
df = kf48()

def run(sgn=+1, look=126, topk=3, hold=21, skip=0, src=None, rets=None):
    sc = sgn*(src.shift(skip).rolling(look).sum())
    r = sc.rank(axis=1, ascending=False); n = sc.shape[1]
    W = pd.DataFrame(0.0, index=sc.index, columns=sc.columns)
    W[r<=topk] = 1.0/topk; W[r>n-topk] = -1.0/topk
    W = W.where(sc.notna(), 0.0)
    d = np.arange(len(W)); reb = (d % hold == 0)
    Wh = W.copy(); Wh[~reb] = np.nan; Wh = Wh.ffill().fillna(0.0)
    return bt(Wh, rets)

rets = df.loc['2008':]
best = (None, -9)
for sgn in [+1,-1]:
    for look in [5,21,63,126,252]:
        for skip in [0,5,21]:
            for hold in [1,5,21]:
                for k in [3,6]:
                    net,_,_ = run(sgn, look, k, hold, skip, df, rets)
                    s = stats(net)
                    if s['sr'] > best[1]: best = ((sgn,look,skip,hold,k), s['sr'], net)
(sgn,look,skip,hold,k), sr, net = best
print(f"BEST idea1/2 cell: sgn={sgn:+d} look={look} skip={skip} hold={hold} k={k} netSR={sr:.2f}")
nvt,_ = vt(net); sv = stats(nvt); g = gates(net)
print(f"VT: ann={sv['ann']:.1f}% mdd={sv['mdd']:.1f}% H1={g['H1']:.2f} H2={g['H2']:.2f} negy={sv['negy']} corrB={g['corr_blend']:+.2f} pass={g['all_pass']}")
