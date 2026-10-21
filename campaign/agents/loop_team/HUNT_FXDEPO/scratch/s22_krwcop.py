"""Last cheap idea: KOP is NOT tradable in reality (Korea capital controls on KRW NDF for
onshore; NDF exists offshore) — but the book is a CROSS (KRW vs SEK etc). Test whether the
edge survives EXCLUDING KRW entirely (pure Scand crosses only — all G10 liquid, tradeable):
books: NO/SF, SD/SF, NO/SD, DN/SF, DN/SD, DN/NO on twelvedata? No — DEX only (SEK=SD, NOK=NO,
CHF=SF, DKK=DN). G10-only 6-book, lb(21,63)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *
import itertools

px=pd.DataFrame({n:dex(n) for n in ['DEXSDUS','DEXSFUS','DEXNOUS','DEXDNUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()
books=[(a,b) for a,b in itertools.combinations(['DEXSDUS','DEXSFUS','DEXNOUS','DEXDNUS'],2)]
rs=[]
for a,b in books:
    sp=lp[a]-lp[b]
    pos=sum(zpos(sp,lb,2.0) for lb in (21,63))/2
    rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
r=pd.concat(rs,axis=1).sum(axis=1)/len(books)
r8=r[r.index>='2008-01-01']
st=full_stats(r8); h1,h2=halves_sr(r8); corr,nc=corr_to(r8,champ)
yr=st['yearly']; neg={k:v for k,v in yr.items() if v<0}
print(f'G10-only 6-book z-rev: SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:.2f}% MDD {st["mdd"]*100:.1f}% negy {len(neg)} {list(neg.values())} corr {corr:+.3f}')
