#!/usr/bin/env python3
"""Localize the max|diff| between my L13 rebuild and committed V2 BAL — find when/where it fails."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from c8_l13 import build13v2
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
A, stA = build13v2(0.07, 0.04)
Bp, stB = build13v2(0.091, 0.03)
BAL = ((A+Bp)/2).dropna()
j = pd.concat([v2.rename('v2'), BAL.rename('mine')], axis=1, join='inner').dropna()
d = (j.v2 - j.mine).abs().sort_values(ascending=False)
print("top-15 rows by |diff|:")
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
for dt in d.index[:15]:
    dv = float(dies[dt]) if dt in dies.index else float('nan')
    cv = float(cfx[dt]) if dt in cfx.index else float('nan')
    print(f"  {dt.date()} v2={j.v2[dt]:+.6f} mine={j.mine[dt]:+.6f} |d|={d[dt]:.6f} dies={dv:+.5f} cfx={cv:+.5f}")
# diff by year
dby = (j.v2-j.mine).abs().groupby(j.index.year).agg(['mean','max','count'])
print("\n|diff| by year:")
print(dby)
# distribution
print("\n|diff| quantiles:", (j.v2-j.mine).abs().quantile([0.5,0.9,0.99,0.999]).values)
print("rows |diff|<1e-12:", int(((j.v2-j.mine).abs()<1e-12).sum()), "of", len(j))
# early rows comparison
print("\nfirst 8 rows: v2 vs mine")
print(j.head(8))
