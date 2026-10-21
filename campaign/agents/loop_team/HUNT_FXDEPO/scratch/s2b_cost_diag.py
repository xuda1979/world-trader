"""Diagnose s2: turnover & gross of the mom book — is it cost death or gross death?"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *
names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
px=pd.DataFrame({n:dex(n) for n in names})
rloc=-px.pct_change()
for lb in [21,63,126]:
    sig=np.sign(px.pct_change(lb))
    ps=sig.shift(1).fillna(0.0)
    gross=(ps*rloc.reindex(px.index).fillna(0.0)).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    r8=gross[gross.index>='2008-01-01']
    t8=turn[turn.index>='2008-01-01']
    print(f'lb{lb}: gross ann {r8.mean()*252*100:+.2f}% | turnover/day {t8.mean():.2f}x | cost drag {t8.mean()*COST*252*100:.2f}%/yr | net {(gross-turn*COST).mean()*252*100:+.2f}%')
