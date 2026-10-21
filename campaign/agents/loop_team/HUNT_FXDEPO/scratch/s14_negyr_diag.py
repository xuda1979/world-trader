"""The KRW3 book fails the neg-yr gate (8 neg yrs, though each >-5% — gate requires <=2).
Diagnose: can a REGIME GATE (vol or rate) lift the neg-yr count without killing SR?
Gates tried (trailing-only, PIT): (a) book's own 63d realized vol on; (b) US 3mo z<threshold;
(c) trade only 2008-2016? no — must be trailing. (d) spread-vol gate (rolling std of spread).
Target: <=2 neg yrs, SR stays >=0.6, H1/H2>=0.3."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]
champ=load_champion()
us=pd.to_numeric(pd.read_csv(f'{FR}/DGS3MO.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna()

def build(gate=None):
    rs=[]; POSs=[]
    for a,b in books:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,2.0) for lb in (21,63))/2
        if gate is not None: pos=pos*gate
        POSs.append(pos)
        rs.append(net_of_book(pd.DataFrame({a:pos,b:-pos}),pd.DataFrame({a:rets[a],b:rets[b]})).fillna(0))
    r=pd.concat(rs,axis=1).sum(axis=1)/3
    return r.dropna(), POSs

def rep(tag, r):
    r8=r[r.index>='2008-01-01']
    st=full_stats(r8); h1,h2=halves_sr(r8)
    yr=st['yearly']; neg={k:v for k,v in yr.items() if v<0}
    corr,nc=corr_to(r8,champ)
    ok=st['sr']>=0.6 and h1>=0.3 and h2>=0.3 and len(neg)<=2 and all(v>-5 for v in neg.values())
    print(f'{tag:34s} SR {st["sr"]:.3f} H1 {h1:.2f} H2 {h2:.2f} ann {st["ann_geo"]*100:5.2f}% MDD {st["mdd"]*100:6.1f}% negy {len(neg)} {list(neg.values())} corr {corr:+.3f} {"** ALL PASS **" if ok else ""}')

# (a) spread-vol gate: trade only when spread 63d vol below its trailing 252d median? Actually
# KRW neg yrs 2013-18 = low-vol drift years -> gate ON when vol HIGH (crisis reversion)?
sp=lp[books[0][0]]-lp[books[0][1]]
vol=sp.rolling(63).std()
volmed=vol.rolling(252).median()
for mult in [1.0,1.1,1.25]:
    gate=(vol>volmed*mult).shift(1).fillna(False)
    gate=pd.Series(gate.astype(float),index=lp.index)
    r,_=build(gate=gate); rep(f'gate: spread63vol>252med*{mult}',r)
# inverse: gate ON when vol LOW
for mult in [1.0,0.9,0.75]:
    gate=(vol<=volmed*mult).shift(1).fillna(False)
    gate=pd.Series(gate.astype(float),index=lp.index)
    r,_=build(gate=gate); rep(f'gate: spread63vol<=252med*{mult}',r)

# (b) DGS3MO z gate
usz=((us-us.rolling(252).mean())/us.rolling(252).std()).reindex(lp.index).ffill()
for thr in [0.5,1.0,-0.5]:
    gate=pd.Series((usz.shift(1)<thr).astype(float),index=lp.index)
    r,_=build(gate=gate); rep(f'gate: us3mo z<{thr}',r)
    gate=pd.Series((usz.shift(1)>thr).astype(float),index=lp.index)
    r,_=build(gate=gate); rep(f'gate: us3mo z>{thr}',r)
