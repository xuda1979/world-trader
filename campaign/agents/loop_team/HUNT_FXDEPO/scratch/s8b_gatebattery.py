"""KRW3 lb(21,63) + KRW/SEK: full charter gate battery (10d-block position-lag scramble)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
LBS=(21,63)

def book_series(a,b,lbs=LBS):
    sp=lp[a]-lp[b]
    pos=sum(zpos(sp,lb) for lb in lbs)/len(lbs)
    P=pd.DataFrame({a:pos,b:-pos})
    R=pd.DataFrame({a:rets[a],b:rets[b]})
    return net_of_book(P,R).dropna(), P, R

# KRW3 composite: EW of 3 books. For scramble: run gate per-book positions jointly.
rets3=[]; PALL=[]; RALL=[]
for a,b in books:
    r,P,R=book_series(a,b)
    rets3.append(r)
    PALL.append(P); RALL.append(R)
tot=sum(r.fillna(0) for r in rets3)/3
r3=tot.dropna()
common=r3.index
POSa=pd.concat([p.reindex(common).fillna(0.0) for p in PALL],axis=1).shift(1).fillna(0.0)
RETa=pd.concat([rr.reindex(common).fillna(0.0) for rr in RALL],axis=1)
# KRW rows duplicated in RETa is fine since POSa also duplicates; pairing consistent
g=gate_battery('KRW3 lb(21,63)', r3, POSa, RETa, champ)
print('yearly:', g['stats']['yearly'])

r1,P1,R1=book_series('DEXKOUS','DEXSDUS')
g1=gate_battery('KRW/SEK lb(21,63)', r1, P1.shift(1).fillna(0.0), R1, champ)
print('yearly:', g1['stats']['yearly'])
