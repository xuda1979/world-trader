"""IDEA 1: EM/Scandinavian FX z-reversion books on DEX crosses (charter idea 1).
Books = spread = ln(P_A/P_B) for correlated pairs; position = clip(-z,±2)/2 per leg.
Grid the space; evaluate SR 2008+.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

# Build close panel: DEX crosses quoted USD per local. All 10 EM/Scand + majors from DEX.
names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS','DEXUSEU','DEXUSUK']
px=pd.DataFrame({n:dex(n) for n in names})
px=px.dropna(how='any')
print('common panel:',px.index[0].date(),px.index[-1].date(),'n=',len(px))

lp=np.log(px)
# candidate spreads: pick pairs with high correlation of daily returns (cointegration proxy)
rets=px.pct_change()
C=rets.corr()
print('\nreturn corr matrix (top abs pairs):')
pairs=[]
for i,a in enumerate(names):
    for b in names[i+1:]:
        c=C.loc[a,b]
        if abs(c)>0.3: pairs.append((a,b,c))
pairs=sorted(pairs,key=lambda x:-abs(x[2]))
for a,b,c in pairs[:15]: print(f'  {a}/{b}: {c:+.3f}')

# z-reversion on each spread, lb in {21,42,63}, per-book SR 2008+
champ=load_champion()
rows=[]
for a,b,c in pairs:
    sp=lp[a]-lp[b]
    for lb in [21,42,63]:
        pos=zpos(sp,lb)
        # book ret: long A short B by pos (pos>0 => long A short B)
        r=net_of_book(pd.DataFrame({a:pos,b:-pos}), rets[[a,b]])
        r8=r[r.index>='2008-01-01'].dropna()
        if len(r8)<1500: continue
        st=full_stats(r8)
        rows.append(dict(pair=f'{a}/{b}',lb=lb,sr=st['sr'],mdd=st['mdd']*100,
                         vol=st['vol']*100,ann=st['ann_geo']*100,negy=st['negy']))
df=pd.DataFrame(rows).sort_values('sr',ascending=False)
print('\nTOP 20 spreads by SR:')
print(df.head(20).to_string(index=False))
df.to_csv('/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch/s1_grid_results.csv',index=False)
