#!/usr/bin/env python3
"""Try V2 recipes: 13-sleeve rows-kept, various slot-weight conventions."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2c_lib as C
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

for MEAN in ['skipna', 'zero']:
    for REBAL in ['formula', 'exact']:
        rA, stA = C.build13(0.07, 0.04, REBAL=REBAL, MEAN=MEAN)
        rB, stB = C.build13(0.091, 0.03, REBAL=REBAL, MEAN=MEAN)
        print(f"MEAN={MEAN} REBAL={REBAL}: SAFE rows {len(rA)}, span {rA.index[0].date()}..{rA.index[-1].date()}, v2rows {len(v2)}")
        for wnew, ntag in [(0.10/12.2, '0.10/12.2'), (0.0455, '0.0455'), (1/22, '1/22'), (0.10/11.2, '0.10/11.2')]:
            for pair in [(rA, rB), ]:
                A = pair[0]; Bp = pair[1]
                D = C.sn_raw(NEW['diescrack']).reindex(v2.index).fillna(0.0)
                X = C.sn_raw(NEW['CFX4']).reindex(v2.index).fillna(0.0)
                # hypothesis A: blend of 13 series each already at own scale: (11*A11 + w*(D+X))/k
                for form in ['slots']:
                    # slots: each FIX engine slot=1, new slot=wnew, total 11+2*wnew, average
                    tot = 11 + 2*wnew
                    candS = (11*A + wnew*(D+X))/tot
                    candA = (11*Bp + wnew*(D+X))/tot
                    cand = ((candS + candA)/2)
                j = pd.concat([v2.rename('v2'), cand.rename('c')], axis=1, join='inner').dropna()
                md = float((j.v2-j.c).abs().max())
                print(f"  wnew={wnew:.5f} ({ntag}): n={len(j)} max|diff|={md:.3e}")
