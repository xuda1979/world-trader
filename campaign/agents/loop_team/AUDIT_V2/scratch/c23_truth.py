#!/usr/bin/env python3
"""DECISIVE test: maybe V2 == committed FIX BAL when slice-scaled. If v2 ≈ a*fix
globally with a≈1, then V2's 11-pool path IS the committed FIX (federal smearing intact),
and slot weights are small add-ons. Check row-wise: v2 - (fix + w*(dies+cfx) + c) residual
structure. Then check WHY residual rms 8e-4: is it vt-global difference (a slightly
different global vt because of the new sleeves in the blend)? Try: recompute the GLOBAL
blend as (11*FIXblend + 0.1*dies08 + 0.1*cfx08)/11.2 where FIXblend is the COMMITTED FIX
pre-cost path? Not recoverable. ALTERNATIVE: fit v2 - fix = w*(dies+cfx) + delta;
if delta ~ -k*fix (proportional drag): regress (v2-fix-w*(d+c)) on fix.
"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies_raw = load(NEW['diescrack']); cfx_raw = load(NEW['CFX4'])
common = v2.index.intersection(fix.index)
j = pd.DataFrame({'v2': v2, 'fix': fix, 'dies': dies_raw, 'cfx': cfx_raw}).loc[common]
j['dies'] = j.dies.fillna(0.0); j['cfx'] = j.cfx.fillna(0.0)
w = 0.023347
resid = j.v2 - j.fix - w*(j.dies + j.cfx)
# regress resid on fix (proportional) and fix^2, and |d fix|
X = np.column_stack([j.fix, (j.fix-j.fix.shift(1)).fillna(0), np.ones(len(j))])
coef, *_ = np.linalg.lstsq(X, resid.values, rcond=None)
r2 = resid.values - X@coef
print(f"resid ~ a*fix + b*dfix + c: a={coef[0]:.5f} b={coef[1]:.5f} c={coef[2]:.2e} resid rms {np.sqrt((r2**2).mean()):.3e}")
# test a=-(1/11.2)*(1 - 11/11.2)? proportional drag hypotheses:
# if V2 11-pool path = FIX * (11/11.2 normalization): a = -0.0179
# Check v2 = fix*(1 - 2*wslot/11.2) + wslot*(dies+cfx) where wslot=0.1/11.2:
for wslot in [0.1/11.2, 0.1/12.2]:
    cand = j.fix*(1-2*wslot) + wslot*(j.dies+j.cfx)
    print(f"wslot={wslot:.5f}: max|v2-cand| {float((j.v2-cand).abs().max()):.3e} rms {float(np.sqrt(((j.v2-cand)**2).mean())):.3e}")
