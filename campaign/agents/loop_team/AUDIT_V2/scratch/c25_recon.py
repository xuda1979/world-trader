#!/usr/bin/env python3
"""PROVENANCE VERDICT: summarize max|diff| of ALL tested recipes. Also do a greedy
column-space check: can v2 (on common 4989 rows) be spanned by {fix, dies, cfx, 1} at
REAL-valued per-row weights? Compute per-row w_i(t) implied by assuming v2 = a*fix + wd*dies + wc*cfx + c(t)?
No — better: fraction of rows where |v2 - fix| > |v2| (sign flips), and quantile of |v2-fix|."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
common = v2.index.intersection(fix.index)
j = pd.DataFrame({'v2': v2, 'fix': fix}).loc[common]
d = (j.v2 - j.fix)
print(f"rows n={len(j)}")
print(f"|v2-fix| quantiles: 50%={d.abs().quantile(.5):.2e} 90%={d.abs().quantile(.9):.2e} 99%={d.abs().quantile(.99):.2e} max={d.abs().max():.2e}")
print(f"rows with |v2-fix|<1e-12: {(d.abs()<1e-12).sum()} ({(d.abs()<1e-12).mean()*100:.1f}%)")
print(f"rows with |v2-fix|<1e-9: {(d.abs()<1e-9).sum()} ({(d.abs()<1e-9).mean()*100:.1f}%)")
print(f"rows with |v2-fix|<1e-6: {(d.abs()<1e-6).sum()} ({(d.abs()<1e-6).mean()*100:.1f}%)")
print(f"rows with |v2-fix|<1e-4: {(d.abs()<1e-4).sum()} ({(d.abs()<1e-4).mean()*100:.1f}%)")
# corr
print(f"corr(v2, fix) = {j.v2.corr(j.fix):.6f}")
# equity curve difference
ev2 = (1+v2).prod(); efix = (1+fix).prod()
print(f"total return: V2 {(ev2-1)*100:.1f}% vs FIX {(efix-1)*100:.1f}% over common rows")
