#!/usr/bin/env python3
"""Check horizon-dependence: does V2's -4.96% DD claim hold for all subwindows, and how does
SAFE/AGGR compare? Also: chunk the difference source — compute what fraction of V2 BAL comes
from each new sleeve (contribution share)."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
r08 = v2[(v2.index >= '2008-03-31') & (v2.index <= '2026-07-31')]
eq = (1+r08).cumprod()
vals = eq.values; n = len(vals)
# worst MaxDD inside ANY 756d window + ALL calendar 3y windows <= wall?
worst = 0; wi = None
for i in range(n-756):
    seg = vals[i:i+757]
    dd = (seg/np.maximum.accumulate(seg)-1).min()
    if dd < worst: worst, wi = dd, eq.index[i]
print(f"worst within-756d DD (2008+): {worst*100:.2f}% start {wi.date()}")
ys = sorted(set(r08.index.year))
w3 = []
for y0 in range(ys[0], ys[-1]-1):
    rr = r08[(r08.index.year >= y0) & (r08.index.year <= y0+2)]
    if len(rr) > 500: w3.append(((1+rr).prod()-1, y0))
w3.sort()
print(f"worst calendar-3y return: {w3[0][0]*100:+.2f}% ({w3[0][1]}..{w3[0][1]+2}); best {w3[-1][0]*100:+.2f}%")
# any negative 3y? any negative 12m window?
neg3 = [x for x in w3 if x[0] < 0]
print(f"negative calendar-3y windows: {len(neg3)}")
w12 = (1+r08).cumprod()/(1+r08).cumprod().shift(252)-1
print(f"worst trailing-252d window: {w12.min()*100:+.2f}% ending {(w12.idxmin()).date()}")
neg12 = (w12.dropna() < 0).sum()
print(f"negative trailing-252d days: {int(neg12)} of {w12.dropna().size}")
