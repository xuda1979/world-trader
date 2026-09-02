#!/usr/bin/env python3
"""AUDIT_V2: the 97 V2-only rows ARE all on the new-sleeve calendar. Which dates are they,
and which are federal holidays (i.e. V2 KEEPS federal holidays, violating the NYSE charter)?
Also compute value composition."""
import numpy as np, pandas as pd, sys, collections
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2lib as L
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = L.load(L.NEW['diescrack']); cfx = L.load(L.NEW['CFX4'])
pool11 = {n: L.sn(p) for n, p in L.POOL.items()}
p11idx = None
for n, s in pool11.items():
    p11idx = s.index if p11idx is None else p11idx.union(s.index)
only = sorted(v2.index.difference(p11idx))
isfed = [d.date() in L.HOL for d in only]
print(f"V2-only: {len(only)} rows; federal holidays among them: {sum(isfed)}")
print("federal ones:", [str(d.date()) for d, f in zip(only, isfed) if f][:20])
nonfed = [d for d, f in zip(only, isfed) if not f]
print(f"non-federal ones: {len(nonfed)}; by weekday: {collections.Counter(d.dayofweek for d in nonfed)}")
print("non-fed sample:", [str(d.date()) for d in nonfed[:10]])
# Values on the federal rows: compare to new-sleeve values
print("\nfederal rows: v2(BAL), v2(SAFE), v2(AGGR), dies, cfx, n11print")
for d in [x for x, f in zip(only, isfed) if f][:10]:
    dv = float(dies.reindex([d]).iloc[0]) if d in dies.index else 0.0
    cv = float(cfx.reindex([d]).iloc[0]) if d in cfx.index else 0.0
    on11 = [n for n, s in pool11.items() if d in s.index]
    print(f"{d.date()} BAL={v2[d]:+.5f} SAFE={v2s[d]:+.5f} AGGR={v2a[d]:+.5f} dies={dv:+.5f} cfx={cv:+.5f} n11={len(on11)} {on11}")
# 2010-12-31 was in the sample — Friday. Check all 58 Monday rows etc.
print("\nnon-fed rows: first 12 with values")
for d in nonfed[:12]:
    dv = float(dies.reindex([d]).iloc[0]) if d in dies.index else 0.0
    cv = float(cfx.reindex([d]).iloc[0]) if d in cfx.index else 0.0
    on11 = [n for n, s in pool11.items() if d in s.index]
    print(f"{d.date()} BAL={v2[d]:+.5f} SAFE={v2s[d]:+.5f} AGGR={v2a[d]:+.5f} dies={dv:+.5f} cfx={cv:+.5f} n11={len(on11)} {on11}")
