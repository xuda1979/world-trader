#!/usr/bin/env python3
"""What fraction of V2 BAL = FIX-pipeline value (not 13-pool)? Compare V2 to committed FIX BAL
row-by-row: fit v2 = a*FIX + w*(dies+cfx) + c. If the 11-pool is UNCHANGED (FIX kept intact,
federal rows smearing etc.), a should be ~ (11/12.2) normalized... etc."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fixs = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fixa = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
sys_path = "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch"
import sys; sys.path.insert(0, sys_path)
from v2lib import NEW, load
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
X = pd.DataFrame({'fix': fix, 'fixs': fixs, 'fixa': fixa,
                  'dies': dies, 'cfx': cfx}).reindex(v2.index)
# 1:1 comparison: on rows where FIX exists, how close is v2 to fix + small new-sleeve add-on?
j = pd.DataFrame({'v2': v2, 'fix': X.fix, 'dies': X.dies, 'cfx': X.cfx}).dropna(subset=['v2','fix'])
j['dies'] = j.dies.fillna(0.0); j['cfx'] = j.cfx.fillna(0.0)
A = np.column_stack([j.fix, j.dies, j.cfx, np.ones(len(j))])
coef, _, _, _ = np.linalg.lstsq(A, j.v2.values, rcond=None)
resid = j.v2.values - A@coef
print(f"v2 ~ a*fix + w_d*dies + w_c*cfx + c: a={coef[0]:.6f} wd={coef[1]:.6f} wc={coef[2]:.6f} c={coef[3]:.2e} resid_max={np.abs(resid).max():.3e}")
A2 = np.column_stack([j.fix.values, j.dies.values, j.cfx.values, j.dies.values*j.cfx.values*0+1, (j.fix.values**2)])
coef2, _, _, _ = np.linalg.lstsq(A2, j.v2.values, rcond=None)
print(f"with fix^2: a={coef2[0]:.6f} b={coef2[4]:.6f} wd={coef2[1]:.6f} wc={coef2[2]:.6f} resid_max={np.abs(j.v2.values - A2@coef2).max():.3e}")
# hypothesis: v2 = (11/11.2)*fix + (0.1/11.2)*(dies+cfx)? try direct arithmetic on FIX blend
for wtot in [11.2, 12.2, 11.0]:
    a = 11.0/wtot
    cand = a*j.fix + (0.10/wtot)*(j.dies+j.cfx)
    md = float((j.v2 - cand).abs().max())
    print(f"v2 = (11/{wtot:.1f})*fix + (0.10/{wtot:.1f})*(dies+cfx): max|diff| {md:.3e}")
# where does fix disagree with v2 most (on common rows)?
d2 = (j.v2 - j.fix).abs().sort_values(ascending=False)
print("\ntop rows |v2-fix| (common):")
for dt in d2.index[:6]:
    print(f"  {dt.date()} v2={j.v2[dt]:+.6f} fix={j.fix[dt]:+.6f} dies={j.dies[dt]:+.5f} cfx={j.cfx[dt]:+.5f}")
