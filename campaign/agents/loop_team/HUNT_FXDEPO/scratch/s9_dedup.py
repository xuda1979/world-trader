"""Cross-check: is the KRW/SEK-style edge just CFX4 with new pairs, or genuinely new?
(a) corr of each KRW book vs CFX4 committed sleeve; (b) marginal value: blend CFX4+KRW3
vs CFX4 alone; (c) plateau across caps/gates for delivery params; (d) LOYO + scrub battery.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
LBS=(21,63)
cfx=pd.read_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv',index_col=0,parse_dates=True).iloc[:,0]

def book_series(a,b,lbs=LBS,cap=2.0):
    sp=lp[a]-lp[b]
    pos=sum(zpos(sp,lb,cap) for lb in lbs)/len(lbs)
    P=pd.DataFrame({a:pos,b:-pos}); R=pd.DataFrame({a:rets[a],b:rets[b]})
    return net_of_book(P,R), P, R

rs=[]
for a,b in books:
    r,_,_=book_series(a,b); rs.append(r.fillna(0))
r3=pd.concat(rs,axis=1).sum(axis=1)/3
j=pd.concat([r3.rename('krw3'),cfx.rename('cfx')],axis=1,join='inner').dropna()
j8=j[j.index>='2008-01-01']
print('corr(KRW3, CFX4) 2008+ common window: %+.4f (n=%d)'%(j8['krw3'].corr(j8['cfx']),len(j8)))

# (b) marginal: CFX4+KRW3 EW vs CFX4 alone (both truncated to common window 2019-09+)
bl=(j8['cfx']+j8['krw3'])/2
for tag,x in [('CFX4 alone',j8['cfx']),('CFX4+KRW3 EW',bl)]:
    st=full_stats(x)
    print(f'{tag}: SR {st["sr"]:.3f} ann {st["ann_geo"]*100:.2f}% MDD {st["mdd"]*100:.2f}% negy {st["negy"]}')

# (c) LOYO on KRW3
print('\nLOYO KRW3 (2008+):')
for y in range(2008,2027):
    m=(r3.index.year!=y)&(r3.index>='2008-01-01')
    st=full_stats(r3[m])
    print(f'  ex-{y}: SR {st["sr"]:.3f}  (n={st["n"]})', end='')
    if (y-2007)%3==0: print()
print()
# (d) scrub-k
r8=r3[r3.index>='2008-01-01']
base=full_stats(r8)['sr']
print('\nscrub-k (drop top-k |ret| days):')
for k in [5,10,20,50]:
    idx=r8.abs().nlargest(k).index
    print(f'  k={k}: SR {full_stats(r8.drop(idx))["sr"]:.3f}')
