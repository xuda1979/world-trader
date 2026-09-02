#!/usr/bin/env python3
"""AUDIT_V2: identify the only-in-V2 rows (97) — new calendar? Which sleeve prints there?"""
import numpy as np, pandas as pd, sys, collections
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2lib as L
ROOT = "/Users/daxu/software/world-trader"

v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
assert (v2.index == v2s.index).all() and (v2.index == v2a.index).all()

# candidate raw calendars of the 13 inputs (unchanged sn calendar = 11-pool)
dies = L.load(L.NEW['diescrack']); cfx = L.load(L.NEW['CFX4'])
pool11 = {n: L.sn(p) for n, p in L.POOL.items()}
p11idx = None
for n, s in pool11.items():
    i = s.index
    p11idx = i if p11idx is None else p11idx.union(i)
newidx = dies.index.union(cfx.index)

only = v2.index.difference(p11idx)
print(f"V2-only rows vs pool11-calendar: {len(only)}")
ino11 = only.intersection(newidx); innew = only.intersection(newidx)
print(f"of those, on new-sleeve calendar: {len(ino11)}")
notonnew = only.difference(newidx)
print(f"V2-only rows NOT on new-sleeve calendar: {len(notonnew)}")
print("sample:", [str(d.date()) for d in sorted(notonnew)[:15]])

# check what V2 prints on those notonnew rows and where the values could come from
vals = v2.reindex(notonnew)
print("\nV2 values on rows not on new calendar (first 15):")
for d, v in vals.items():
    dv = dies.reindex([d]); cv = cfx.reindex([d])
    on11 = [n for n, s in pool11.items() if d in s.index]
    print(f"{d.date()} v2={v:+.6f} dies={float(dv.iloc[0]) if len(dv) else 'NA'} cfx={float(cv.iloc[0]) if len(cv) else 'NA'} n11print={len(on11)} {on11}")
