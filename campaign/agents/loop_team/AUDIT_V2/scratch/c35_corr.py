#!/usr/bin/env python3
"""Correlation of new sleeves to champion pool + yearly contributions in V2 + tail-year checks."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
print("corr(dies, CFX4):", float(pd.concat([dies, cfx], axis=1, join='inner').dropna().corr().iloc[0,1]).__round__(4))
# 2008+ scoped
r08 = v2[(v2.index >= '2008-03-31')]
yr = r08.groupby(r08.index.year).apply(lambda x: (1+x).prod()-1)
print("V2 BAL yearly (2008+):", {int(k): round(v*100,1) for k, v in yr.items()})
# best days / worst days
print("\ntop-5 V2 BAL days:")
o = v2.abs().sort_values(ascending=False).index[:5]
for d in sorted(o):
    print(f"  {d.date()} {v2[d]*100:+.2f}%")
# contribution of 2026 tail beyond 07-31
tail = v2[v2.index > '2026-07-31']
eqtail = (1+tail).prod()-1
print(f"\n2026 tail beyond 07-31: {eqtail*100:+.2f}% over {len(tail)} days (thin-sleeve rows?)")
cfx_tail = cfx[(cfx.index > '2026-07-31')]
print(f"CFX4 has {len(cfx_tail)} rows in tail; diescrack {len(dies[dies.index > '2026-07-31'])}")
# 11-pool rows in tail: how many sleeves print on last 10 rows?
R11 = {n: load(p) for n, p in POOL11.items()}
for d in v2.index[-5:]:
    cnt11 = sum(1 for s in R11.values() if d in s.index)
    print(f"  {d.date()}: {cnt11}/11 pool sleeves print")
