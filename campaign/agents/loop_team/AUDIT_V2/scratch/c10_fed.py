#!/usr/bin/env python3
"""On federal rows: what exactly does V2 print vs my rebuild? Is it a cost term?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from c8_l13 import build13v2
ROOT = "/Users/daxu/software/world-trader"
from v2lib import HOL
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
A, stA = build13v2(0.07, 0.04)
Bp, stB = build13v2(0.091, 0.03)
BAL = ((A+Bp)/2).dropna()
fed = [d for d in v2.index if d.date() in HOL]
print(f"federal rows in V2: {len(fed)}")
rows = []
for d in fed:
    rows.append((d.date(), float(v2[d]), float(BAL[d]) if d in BAL.index else np.nan,
                 float(stA['sc'][d]) if d in stA['sc'].index else np.nan))
df = pd.DataFrame(rows, columns=['date','v2','mine','sc']).set_index('date')
print(df.head(12).to_string())
print(f"\nv2 on fed rows: mean {df.v2.mean():.6f} min {df.v2.min():.6f} max {df.v2.max():.6f}")
print(f"nonzero (>1e-10) fed rows: {(df.v2.abs()>1e-10).sum()} of {len(df)}")
print(f"mine on fed rows nonzero: {(df.mine.abs()>1e-10).sum()}")
# what about the value distribution - all ~ -0.00058?
print("\nv2 fed-row values sorted, count of each distinct rounded value:")
vc = df.v2.round(6).value_counts()
print(vc.head(10))
