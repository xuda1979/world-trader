"""CANDIDATE 5 (ROBUSTNESS): A+D poolvt08cap3 across:
- start cuts (2020+,2022+), recent-only SR (2022+,2024+), H2 recomputed 2017+
- parameter plateau: rv window 42/63/126, thA in (-0.25,0,0.25), thD (0.25,0.5,0.75), vix ma 126/252/504
- cost stress: 6bps->10bps, 15bps; borrow 0.5%->1%
- threshold-cliff: population of on-days (gate fraction)
- scrub top-5/10 days, LOYO worst-year removal
- DSR-style: block-boot CI on SR (2000x 10d blocks)"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv252=(V-V.rolling(252).mean())/V.rolling(252).std()

def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    net=p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*p.clip(upper=0.0).abs()
    return net.dropna()
def poolvt(r, tgt=0.08, cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (r*((tgt/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()

def build(winA=63,winD=63,thA=0.0,thD=0.5,ma_v=252,cost_bps=6.0,borrow=0.005):
    zA=rz(MOM,winA); zD=rz(MKT,winD)
    V2=vix.reindex(MKT.index).ffill()
    zv=(V2-V2.rolling(ma_v).mean())/V2.rolling(ma_v).std()
    posA=pd.Series(np.where(zA.shift(1)<thA,1.0,0.0),index=MOM.index)
    posD=pd.Series(np.where((zD.shift(1)<thD)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
    pA=posA.shift(1).reindex(MOM.index); pD=posD.shift(1).reindex(MKT.index)
    cb=cost_bps/1e4; brr=borrow/252
    netA=pA*MOM-(pA.diff().abs()/2.0).fillna(0)*cb
    netD=pD*MKT-(pD.diff().abs()/2.0).fillna(0)*cb-brr*pD.clip(upper=0).abs()
    bl=((netA+netD)/2).dropna()
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    return poolvt(bl)

base=build()
print('=== start cuts / subperiods (SR) ===')
for cut in ['2008-01-01','2010-01-01','2017-01-01','2020-01-01','2022-01-01','2024-01-01']:
    x=base[base.index>=cut]
    st=lib.full_stats(x)
    print(f"  {cut}+: SR {st['sr']:.3f} n={st['n']} ann {st['ann_geo']:.1%} negy {st['negy']}")
mid=base.index[len(base)//2]
print('H1 %.2f H2 %.2f'%(lib.full_stats(base[base.index<=mid])['sr'],lib.full_stats(base[base.index>mid])['sr']))
h2x=base[base.index>=pd.Timestamp('2017-01-01')]
print('2017+ SR %.3f'%h2x.mean()/1) if False else print('2017+ SR %.3f'%(h2x.mean()/h2x.std()*np.sqrt(252)))

print('\n=== parameter plateau (SR) ===')
for winA in (42,63,126):
    print(f"  winA={winA}: SR {build(winA=winA).mean()/build(winA=winA).std()*np.sqrt(252):.3f}")
for thA in (-0.25,0.0,0.25):
    print(f"  thA={thA}: SR {build(thA=thA).mean()/build(thA=thA).std()*np.sqrt(252):.3f}")
for thD in (0.25,0.5,0.75):
    print(f"  thD={thD}: SR {build(thD=thD).mean()/build(thD=thD).std()*np.sqrt(252):.3f}")
for ma in (126,252,504):
    print(f"  vix_ma={ma}: SR {build(ma_v=ma).mean()/build(ma_v=ma).std()*np.sqrt(252):.3f}")
print('\n=== cost stress ===')
for cb,br in [(6,0.005),(10,0.005),(15,0.005),(6,0.01)]:
    x=build(cost_bps=cb,borrow=br)
    print(f"  cost {cb}bps borrow {br:.1%}: SR {x.mean()/x.std()*np.sqrt(252):.3f}")

print('\n=== gate fraction ===')
zA=rz(MOM,63); V2=vix.reindex(MKT.index).ffill()
zv=(V2-V2.rolling(252).mean())/V2.rolling(252).std()
posA=(zA.shift(1)<0.0); posD=(rz(MKT,63).shift(1)<0.5)&(zv.shift(1)<0.0)
both=posA.reindex(base.index).fillna(False)
print('bookA on-frac %.2f bookD on-frac %.2f (2008+)'%(posA[posA.index>='2008-01-01'].mean(),
      posD[posD.index>='2008-01-01'].mean()))

print('\n=== scrub / LOYO ===')
def sr(x): return x.mean()/x.std()*np.sqrt(252)
for k in (5,10,20):
    v=base.values.copy(); o=np.argsort(v)[::-1]
    v[o[:k]]=0
    print(f"  scrub top{k}: SR {sr(pd.Series(v,index=base.index)):.3f}")
for y in range(2008,2027):
    x=base[base.index.year!=y]
    pass
loyo={y:sr(base[base.index.year!=y]) for y in (2015,2020,2022,2024)}
print('  LOYO (drop yr):',{k:round(v,3) for k,v in loyo.items()})

print('\n=== block-boot CI on SR ===')
rng=np.random.default_rng(3); x=base.values; T=len(x); nb=T//10
srs=[]
for _ in range(2000):
    st_=rng.integers(0,T-10,size=nb)
    xb=np.concatenate([x[s:s+10] for s in st_])[:T]
    if xb.std()>0: srs.append(xb.mean()/xb.std()*np.sqrt(252))
srs=np.array(srs)
print(f"  SR real {base.mean()/base.std()*np.sqrt(252):.3f} boot CI [{np.percentile(srs,2.5):.3f},{np.percentile(srs,97.5):.3f}]")
