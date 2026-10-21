"""OOS honesty: the KRW3 book params were picked on the FULL sample (lb21 best in s1 grid).
IS/OOS: pick best lb on IS 2008-2015, evaluate 2016+. Also start-cut robustness 2016+/2020+.
And OOS17 check like champion convention: 2017+ arithmetic."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
def build(lbs,cap=2.0):
    rs=[]
    for a,b in books:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,cap) for lb in lbs)/len(lbs)
        rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
    return pd.concat(rs,axis=1).sum(axis=1)/len(books)

print('IS (2008-2015) lb selection:')
best=None
for lbs in [(10,),(21,),(42,),(63,),(21,63),(21,42,63),(10,21),(10,21,42)]:
    r=build(lbs); is_=r[(r.index>='2008-01-01')&(r.index<'2016-01-01')]
    sr=full_stats(is_)['sr']
    print(f'  lb{lbs}: IS SR {sr:.3f}')
    if best is None or sr>best[1]: best=(lbs,sr)
print('best on IS:',best)
lbs=best[0]
r=build(lbs)
for cut,tag in [('2008-01-01','full08+'),('2016-01-01','OOS16+'),('2017-01-01','OOS17+'),('2020-01-01','OOS20+'),('2023-01-01','OOS23+')]:
    x=r[r.index>=cut]
    st=full_stats(x)
    print(f'{tag}: SR {st["sr"]:.3f} ann_geo {st["ann_geo"]*100:.2f}% MDD {st["mdd"]*100:.1f}% negy {st["negy"]} n={st["n"]}')
