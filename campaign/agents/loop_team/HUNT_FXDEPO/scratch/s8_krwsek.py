"""KRW/SEK lb21 z-rev — the ONE DEX book family with SR~0.8. Full battery + robustness:
caps, lb plateau, dual-tf, gate variants, then full charter gates incl 10d-block pos-lag scramble.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS','DEXBZUS','DEXMXUS']})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()

def zpos_w(sp, lbs, cap=2.0):
    return sum(zpos(sp,lb,cap) for lb in lbs)/len(lbs)

def krwsek_book(lbs, cap=2.0):
    sp=lp['DEXKOUS']-lp['DEXSDUS']
    pos=zpos_w(sp,lbs,cap)
    r=net_of_book(pd.DataFrame({'K':pos,'S':-pos}),pd.DataFrame({'K':rets['DEXKOUS'],'S':rets['DEXSDUS']}))
    return r.dropna(), pos

# 3-book family: KRW/SEK + KRW/CHF + KRW/NOK (each lb21)? Test EW composite
def krw3_book(lbs, cap=2.0):
    books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
    tot=0
    for a,b in books:
        sp=lp[a]-lp[b]
        pos=zpos_w(sp,lbs,cap)
        r=net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]}))
        tot=tot+r.fillna(0)
    return (tot/len(books)).dropna()

print('--- plateau: KRW/SEK single book ---')
for lbs in [(21,),(42,),(63,),(10,),(21,63),(21,42,63)]:
    r,_=krwsek_book(lbs)
    r8=r[r.index>='2008-01-01']
    st=full_stats(r8); h1,h2=halves_sr(r8)
    print(f'lb{lbs}: SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:.2f}% MDD {st["mdd"]*100:.1f}% negy {st["negy"]}')
print('--- plateau: KRW3 composite ---')
for lbs in [(21,),(42,),(63,),(21,63)]:
    r=krw3_book(lbs)
    r8=r[r.index>='2008-01-01']
    st=full_stats(r8); h1,h2=halves_sr(r8)
    print(f'lb{lbs}: SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:.2f}% MDD {st["mdd"]*100:.1f}% negy {st["negy"]}')
