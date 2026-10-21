#!/usr/bin/env python3
"""Try: allweeks calendar 11-pool + new sleeves at candidate weights; compare to V2."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2b_lib as B
from v2lib import NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])

for rebal in ['formula', 'exact']:
    r11, st = B.build(0.07, 0.04, REBAL=rebal)
    r11B, stB = B.build(0.091, 0.03, REBAL=rebal)
    print(f"REBAL={rebal}: 11-pool allweeks calendar: SAFE rows {len(r11)}, span {r11.index[0].date()}..{r11.index[-1].date()}")
    # try slot weights: r_v2 = (11*r11_fixed? ...)
    for wnew in [0.10/12.2, 0.10/11.2, 0.0455, 0.04545, 1/22, 0.04]:
        # hypothesis: r = (sum over 11 at w=1 + wnew*dies + wnew*cfx)/ (11+2*wnew)? normalized
        for norm, ntag in [(True, 'norm'), (False, 'nonorm')]:
            tot = 11 + 2*wnew
            cand = (11*r11.reindex(v2.index).fillna(0) + 1/r11.max()*0)  # placeholder
            # build directly
            A = r11.reindex(v2.index).fillna(0.0)
            Bp = r11B.reindex(v2.index).fillna(0.0)
            D = dies.reindex(v2.index).fillna(0.0)
            C = cfx.reindex(v2.index).fillna(0.0)
            if norm:
                cand = (11*A + Bp + wnew*(D+C)) / tot
            else:
                cand = (A + Bp)/2 + wnew*(D+C)
            j = pd.concat([v2.rename('v2'), cand.rename('c')], axis=1, join='inner').dropna()
            md = float((j.v2-j.c).abs().max())
            print(f"  rebal={rebal} wnew={wnew:.5f} {ntag}: n={len(j)} max|diff|={md:.3e}")
