"""Also check the OOS-selected variant lb(10,21,42): does it pass more gates?
And verdict on which variant (if any) to DELIVER as candidate. Full battery on lb(10,21,42)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
LBS=(10,21,42)
rs=[]; PALL=[]; RALL=[]
for i,(a,b) in enumerate(books):
    sp=lp[a]-lp[b]
    pos=sum(zpos(sp,lb,2.0) for lb in LBS)/len(LBS)
    P=pd.DataFrame({f'B{i}_L':pos,f'B{i}_S':-pos})
    R=pd.DataFrame({f'B{i}_L':rets[a],f'B{i}_S':rets[b]})
    rs.append(net_of_book(P,R)); PALL.append(P); RALL.append(R)
r=pd.concat([x.fillna(0) for x in rs],axis=1).sum(axis=1)/3
r8=r[r.index>='2008-01-01']
common=r8.index
POSa=pd.concat([p.reindex(common).fillna(0) for p in PALL],axis=1).shift(1).fillna(0)
RETa=pd.concat([rr.reindex(common).fillna(0) for rr in RALL],axis=1)[POSa.columns]
g=gate_battery('KRW3 lb(10,21,42) [IS-picked]', r8, POSa, RETa, champ)
print('yearly:',g['stats']['yearly'])
