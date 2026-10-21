#!/usr/bin/env python3
"""Histogram of |V2 BAL| daily returns; check the -5.8bp modal cost; verify cost-only rows in FIX."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
print("V2 BAL |r| quantiles:", v2.abs().quantile([0.01,0.05,0.1,0.25,0.5]).values)
print("V2 rows |r| in [1e-5, 3e-4]:", int(((v2.abs()>1e-5)&(v2.abs()<3e-4)).sum()))
print("V2 rows |r| < 1e-5:", int((v2.abs()<1e-5).sum()))
print("FIX rows |r| in [1e-5,3e-4]:", int(((fix.abs()>1e-5)&(fix.abs()<3e-4)).sum()))
# distinct-value counts near the modal cost
print("\nmost common rounded values in V2 BAL (1e-6 bins):")
print((v2*1e6).round(1).value_counts().head(10))
# where does SAFE==AGGR happen in V2?
same = (v2s - v2a).abs() < 1e-12
print(f"\nSAFE==AGGR rows: {int(same.sum())} of {len(v2)}")
fsame = same[same].index
print("by year:", pd.Series([d.year for d in fsame]).value_counts().sort_index().to_dict())
# same in FIX?
fs = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fa = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
samef = (fs-fa).abs() < 1e-12
print(f"FIX SAFE==AGGR rows: {int(samef.sum())} of {len(fs)}")
