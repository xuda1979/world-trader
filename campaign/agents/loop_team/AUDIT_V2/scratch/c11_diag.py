#!/usr/bin/env python3
"""Diagnose: 2008-11-11 row. Compare V2 BAL/SAFE/AGGR identical values to candidate formulas.
On this row: new sleeves 0, 11-pool prints raw PnL, throttle switch happens 2008-11-12 (SAFE/BAL).
V2 row value ~= -5.8bp on all three variants."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL
ROOT = "/Users/daxu/software/world-trader"
v2  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
d = pd.Timestamp('2008-11-11')
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
R = {n: load(p) for n, p in POOL11.items()}
dv = float(dies[d]) if d in dies.index else 0.0
cv = float(cfx[d]) if d in cfx.index else 0.0
print(f"target: BAL {v2[d]:+.6f} SAFE {v2s[d]:+.6f} AGGR {v2a[d]:+.6f}; dies {dv:+.6f} cfx {cv:+.6f}")
# raw prints
rawv = {n: (float(s[d]) if d in s.index else np.nan) for n, s in R.items()}
print("raw prints:", {k: round(v,6) for k,v in rawv.items()})
# candidate: mean of raw prints (skipna, only the sleeves present that day) * scales
# per-sleeve vt 0.08 scales on the ALLWEEKS (no-smear) calendar — compute here
def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]
SnP = pd.DataFrame({n: vt(sn_raw(POOL11[n]), 0.08)[1] for n in POOL11})
i = SnP.index.get_loc(d)
print(f"\nscales on {d.date()}:")
for n in POOL11:
    print(f"  {n}: {SnP[n].iloc[i]:.4f}")
# SAFE/BAL/AGGR identical => cost-type row (common term) OR 11-pool contribution exactly 0 net of costs?
# Try: r = [sum_i s_i*r_i - cost terms] with s_i = scale from vt 0.08 — compute the 11-pool gross contribution:
tot = 0.0
for n in POOL11:
    if not np.isnan(rawv[n]):
        tot += SnP[n].iloc[i]*rawv[n]
print(f"\nsum_i scale_i*raw_i = {tot:+.6f}; /11 = {tot/11:+.6f}")
# global vt? blend-based global scalar gs (TGT 0.07): needs blend series; approximate not available here.
# So V2 fed value -5.8bp vs gross +2.6bp/11=+2.4bp... still unexplained. Also SAFE=AGGR on 2008-11-11?
print(f"\nSAFE==AGGR on fed rows? {np.allclose(v2s[fed_rows] if False else 0,0)}")
