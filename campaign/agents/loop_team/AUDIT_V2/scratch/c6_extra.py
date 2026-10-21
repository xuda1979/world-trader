#!/usr/bin/env python3
"""Which Mon-Fri rows does V2 drop that allweeks-11pool has? (108 rows)"""
import numpy as np, pandas as pd, sys, collections
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2b_lib as B
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
r11, st = B.build(0.07, 0.04, REBAL='formula')
extra = r11.index.difference(v2.index)
print(f"allweeks-extra rows (in my allweeks 11-pool, not in V2): {len(extra)}")
print("by weekday:", collections.Counter(d.dayofweek for d in extra))
pass
try:
    from v2lib import HOL
    fed = [d for d in extra if d.date() in HOL]
    print(f"federal among extra: {len(fed)}")
    print("fed sample:", [str(d.date()) for d in fed[:10]])
except ImportError:
    pass
nonfed = [d for d in extra if d.date() not in HOL]
print(f"non-fed among extra: {len(nonfed)}")
print("non-fed sample:", [str(d.date()) for d in nonfed[:15]])
print("non-fed by year:", collections.Counter(d.year for d in nonfed))
print("non-fed by weekday:", collections.Counter(d.dayofweek for d in nonfed))
# are non-fed ones Good Friday etc? check day-after values in v2 vs raw
raw = {n: load(p) for n, p in __import__('v2lib').POOL.items()}
print("\nfirst 8 non-fed extra rows: raw prints count")
for d in nonfed[:8]:
    on = [n for n, s in raw.items() if d in s.index]
    print(f"{d.date()} n_raw_print={len(on)} {on} v2_has={d in v2.index}")
