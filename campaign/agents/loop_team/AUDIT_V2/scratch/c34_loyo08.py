#!/usr/bin/env python3
"""LOYO part 2: scoped 2008+ — does every drop keep 0/19? Also find which year is the neg one
in full span (2006 stub) and verify it's the warmup stub. Also 1 neg-yr identity across drops."""
import numpy as np, pandas as pd, sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
exec(open('/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch/c33_sweeps.py').read().split("# baseline")[0])

print("LOYO scoped 2008-01-01..2026-07-31:")
worst = []
for dn in sorted(set(POOL11) | set(NEW)):
    A = build(0.07, 0.04, drop={dn}); B = build(0.091, 0.03, drop={dn})
    BAL = ((A+B)/2).dropna()
    BAL = BAL[(BAL.index >= '2008-01-01') & (BAL.index <= '2026-07-31')]
    srd, srm, mdd, ann, neg, ny = stats(BAL)
    yr = BAL.groupby(BAL.index.year).apply(lambda x: (1+x).prod()-1)
    worst.append((yr.min(), dn, srd, mdd))
    print(f"  -{dn:10s}: ann {ann:6.2f}% SR_d {srd:.3f} MDD {mdd:6.2f}% neg {neg}/{ny} worst-yr {yr.min()*100:+.2f}%")
worst.sort()
print(f"\nworst yearly return across LOYO: {worst[0][0]*100:+.2f}% (-{worst[0][1]})")
# baseline 2008+ scoped
A = build(0.07, 0.04); B = build(0.091, 0.03); BAL = ((A+B)/2).dropna()
BAL = BAL[(BAL.index >= '2008-01-01') & (BAL.index <= '2026-07-31')]
srd, srm, mdd, ann, neg, ny = stats(BAL)
yr = BAL.groupby(BAL.index.year).apply(lambda x: (1+x).prod()-1)
print(f"baseline scoped: ann {ann:.2f}% SR_d {srd:.3f} MDD {mdd:.2f}% neg {neg}/{ny} worst {yr.min()*100:+.2f}%")
