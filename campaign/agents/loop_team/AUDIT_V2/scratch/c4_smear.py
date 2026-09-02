#!/usr/bin/env python3
"""AUDIT_V2: examine raw 11-pool values on federal rows vs V2 values, and the day-after diff."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2lib as L
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = L.load(L.NEW['diescrack']); cfx = L.load(L.NEW['CFX4'])
raw = {n: L.load(p) for n, p in L.POOL.items()}
fedrows = [d for d in v2.index if d.date() in L.HOL][:8]
for d in fedrows:
    nxt = d + pd.Timedelta(days=1)
    print(f"\n=== {d.date()} (fed) and {nxt.date()} ===")
    print(f"V2 BAL {d.date()}: {v2[d]:+.6f} | V2 SAFE {v2s[d]:+.6f} | V2 AGGR {v2a[d]:+.6f}")
    for n, s in raw.items():
        if d in s.index:
            print(f"  raw {n}: {d.date()}={s[d]:+.6f}  {nxt.date()}={s[nxt] if nxt in s.index else float('nan'):+.6f}")
    if d in fix.index: print(f"  FIX BAL {d.date()}: {fix[d]:+.6f}")
    if nxt in fix.index: print(f"  FIX BAL {nxt.date()}: {fix[nxt]:+.6f}")
    if nxt in v2.index: print(f"  V2  BAL {nxt.date()}: {v2[nxt]:+.6f}")
    dv = float(dies[d]) if d in dies.index else 0.0
    cv = float(cfx[d]) if d in cfx.index else 0.0
    print(f"  dies {dv:+.6f} cfx {cv:+.6f}")
