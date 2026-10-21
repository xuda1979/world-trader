#!/usr/bin/env python3
"""What sleeves print on federal rows? Is a6r7 present there? What values explain -5.8bp?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, load, vt
ROOT = "/Users/daxu/software/world-trader"
v2  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
R = {n: load(p) for n, p in POOL11.items()}
fed = [d for d in v2.index if d.date() in HOL] if False else [d for d in v2.index if d.date() in __import__('v2lib').HOL]
def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]
SnP = pd.DataFrame({n: vt(sn_raw(POOL11[n]), 0.08)[1] for n in POOL11})
dies08 = vt(sn_raw(NEW['diescrack']), 0.08)[0]
cfx08 = vt(sn_raw(NEW['CFX4']), 0.08)[0]
W = SnP.div(SnP.sum(axis=1), axis=0)
print("fed-row | v2_BAL | v2_SAFE | v2_AGGR | a6r7? | W*raw sum (11vt) | 13-mean est")
for d in fed[:6]:
    rawv = {n: (float(R[n][d]) if d in R[n].index else np.nan) for n in POOL11}
    nprint = sum(1 for v in rawv.values() if not np.isnan(v))
    a6 = rawv.get('a6r7', np.nan)
    wsum = sum(W[n][d]*rawv[n] for n in POOL11 if not np.isnan(rawv[n]))
    print(f"{d.date()} {v2[d]:+.6f} {v2s[d]:+.6f} {v2a[d]:+.6f} a6r7={a6 if not np.isnan(a6) else 'NA'} nprint={nprint} wsum={wsum:+.6f}")
# check the 2008-11-11 row more: is v2 == -(borrow+reb cost) only?
d = fed[1]
print(f"\n2008-11-11: v2 {v2[d]:+.6f}")
print("raw QAxasts print:", float(R['QAxasts'][d]), "carryv2:", float(R['carryv2'][d]))
# SnP scale x raw for each present sleeve:
for n in ['QAxasts','carryv2','dualmom','C5ng','C5ngsum','brwt10']:
    print(f"  {n}: scale {SnP[n][d]:.4f} raw {R[n][d] if d in R[n].index else 'NA'} contrib/11 {SnP[n][d]*float(R[n][d])/11:+.6f}" if d in R[n].index else f"  {n}: NA")
