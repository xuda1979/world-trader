"""Extended DEX z-book variants: (a) all-10-pair EW portfolio (like CFX4 style), (b) cap/gate
variants on the best DEX books, (c) DEX vs majors synthetics (e.g. KRW via USDJPY*USDKRW? not
constructible), (d) DEX momentum 5d SHORT-horizon (coord_emfx used 21+; try 3/5/10 with vt).
Also the EM dollar-index z-rev: basket = mean of ln DEXEM; short-horizon reversion of EM basket.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

names=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS','DEXJPUS','DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
px=pd.DataFrame({n:dex(n) for n in names})
lp=np.log(px); rets=px.pct_change()
champ=load_champion()

def zpos_cap(spread, lb, cap=2.0, gate=0.0):
    m=spread.rolling(lb).mean(); s=spread.rolling(lb).std()
    z=(spread-m)/s
    w=(-(z/cap)).clip(-0.5,0.5)
    if gate>0: w=w.where(z.abs()>=gate,0.0)
    return w

# (a) top-5 book EW (KRWSD, KRWSF, KRWNO, BZSF, MXKO) at their best lb
top=[('DEXKOUS','DEXSDUS',21),('DEXKOUS','DEXSFUS',21),('DEXKOUS','DEXNOUS',21),
     ('DEXBZUS','DEXSFUS',42),('DEXMXUS','DEXKOUS',21)]
tot=0; 
for a,b,lb in top:
    sp=lp[a]-lp[b]
    pos=zpos_cap(sp,lb)
    r=net_of_book(pd.DataFrame({a:pos,b:-pos}),rets[[a,b]])
    tot=tot+r.fillna(0)
r5=(tot/len(top)).dropna()
print('=== top5 DEX z-book EW ==='); 
print(gate_line:='')

def show(tag,r):
    r8=r[r.index>='2008-01-01'].dropna()
    if len(r8)<800: print(tag,'too short',len(r8)); return None
    st=full_stats(r8); h1,h2=halves_sr(r8); corr,nc=corr_to(r8,champ)
    print(f'{tag:38s} SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:5.2f}% MDD {st["mdd"]*100:6.1f}% negy {st["negy"]} corr {corr:+.3f} n={len(r8)}')
    return r8
show('top5 DEX z-book EW',r5)

# (b) gate variants on KRW/SDU
a,b='DEXKOUS','DEXSDUS'; sp=lp[a]-lp[b]
for lb in [21]:
    for cap in [1.0,1.5,2.0]:
        for gate in [0.0,0.5,1.0,1.5]:
            pos=zpos_cap(sp,lb,cap,gate)
            r=net_of_book(pd.DataFrame({a:pos,b:-pos}),rets[[a,b]])
            show(f'KRW/SEK lb{lb} cap{cap} gate{gate}',r)

# (e) EM basket short-horizon reversion: basket = EW ln(DEX EM 5) z
em=['DEXBZUS','DEXMXUS','DEXKOUS','DEXINUS','DEXSIUS']
bask=lp[em].mean(axis=1)
for lb in [10,21,42]:
    pos=zpos_cap(bask,lb)
    r=net_of_book(pd.DataFrame({n:pos/len(em) for n in em}),
                  pd.DataFrame({n:rets[n] for n in em}))
    show(f'EM basket z-rev lb{lb}',r)

# (f) Scand basket z-rev
sc=['DEXNOUS','DEXSDUS','DEXSFUS','DEXDNUS']
bask=lp[sc].mean(axis=1)
for lb in [10,21,42]:
    pos=zpos_cap(bask,lb)
    r=net_of_book(pd.DataFrame({n:pos/len(sc) for n in sc}),
                  pd.DataFrame({n:rets[n] for n in sc}))
    show(f'Scand basket z-rev lb{lb}',r)
