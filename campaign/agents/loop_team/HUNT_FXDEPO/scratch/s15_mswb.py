"""Mean-spreading variant: instead of fixed lb z, use expanding mean/std z, or a 6-book
inclusion (add KRW/JPY? no JPY-KRW cross on DEX — both vs USD is fine: spread ln(KO)-ln(JP)).
Try ALL KRW/NOK/SEK/CHF combinations to diversify the 3 books:
books: KO/SD, KO/SF, KO/NO, SD/SF, SD/NO, NO/SF — 6 books, EW.
Each z lb(21,63) cap2. More books = smoother, fewer neg yrs?"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *
import itertools

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()
allb=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS'),
      ('DEXSDUS','DEXSFUS'),('DEXSDUS','DEXNOUS'),('DEXNOUS','DEXSFUS')]

def build(booklist, lbs=(21,63), cap=2.0, gate=None):
    rs=[]; POSs=[]
    for a,b in booklist:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,cap) for lb in lbs)/len(lbs)
        if gate is not None: pos=pos*gate
        POSs.append(pos)
        rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
    r=pd.concat(rs,axis=1).sum(axis=1)/len(booklist)
    return r.dropna(), POSs

def rep(tag, r):
    r8=r[r.index>='2008-01-01']
    st=full_stats(r8); h1,h2=halves_sr(r8)
    yr=st['yearly']; neg={k:v for k,v in yr.items() if v<0}
    corr,nc=corr_to(r8,champ)
    ok=st['sr']>=0.6 and h1>=0.3 and h2>=0.3 and len(neg)<=2 and all(v>-5 for v in neg.values())
    print(f'{tag:34s} SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:5.2f}% MDD {st["mdd"]*100:6.1f}% negy {len(neg)} {list(neg.values())} corr {corr:+.3f} {"** ALL PASS **" if ok else ""}')
    return st

r6,_=build(allb); rep('6-book Scand+KRW EW', r6)
# 4-book without NOK pairs
b4=allb[:3]+[(('DEXSDUS','DEXSFUS'))]
r4,_=build(b4); rep('4-book (+SD/SF)', r4)
# single best books standalone
for a,b in allb:
    r1,_=build([(a,b)]); rep(f'single {a[-4:]}/{b[-4:]}', r1)
