"""FINAL 4: lock in remaining audit numbers for FINDINGS:
(1) SR monthly + block-boot CI (poolvt), (2) distinct-values/flatten summary,
(3) full yearly table poolvt, (4) the champion-overlap span arithmetic (champion 2026-07/08
months absent from sleeve: data-end 2026-06-30 disclosure), (5) gross-exposure estimate,
(6) header of delivered CSVs for provenance"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

pv=pd.read_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',index_col=0,parse_dates=True)['ret']
champ=lib.load_champion()
# monthly SR
m=(1+pv).resample('ME').prod()-1
sr_m=m.mean()/m.std()*np.sqrt(12)
print('SR_m %.4f (n=%d months)'%(sr_m,len(m)))
# block boot CI 2000x
rng=np.random.default_rng(5); x=pv.values; T=len(x); nb=T//10
srs=[]
for _ in range(2000):
    st_=rng.integers(0,T-10,size=nb)
    xb=np.concatenate([x[s:s+10] for s in st_])[:T]
    srs.append(xb.mean()/xb.std()*np.sqrt(252))
srs=np.array(srs)
print('block-boot(10d,2000x) SR CI [%.3f, %.3f]'%(np.percentile(srs,2.5),np.percentile(srs,97.5)))
# yearly
yr=pv.groupby(pv.index.year).apply(lambda g:(1+g).prod()-1)
print('yearly:',{int(k):round(v*100,2) for k,v in yr.items()})
# months missing vs champion
champ_end=champ.index.max(); pv_end=pv.index.max()
print('champion ends',champ_end.date(),'sleeve ends',pv_end.date(),'-> sleeve misses last',
      len(champ[champ.index>pv_end]),'champion days (2026-07/08, FF data vintage 202606)')
# gross exposure proxy: fraction of days with at least one book on + average books on
ff=lib.load_ff3(); mom=lib.load_mom()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix_=lib.load_vix().reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()
onA=(rz(MOM).shift(1)<0.0).reindex(pv.index).fillna(False)
onD=((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0)).reindex(pv.index).fillna(False)
print('days on: A %.1f%% D %.1f%% both %.1f%% neither %.1f%%'%(onA.mean()*100,onD.mean()*100,
      (onA&onD).mean()*100,(~onA&~onD).mean()*100))
print('implied gross notional: 0.5*(A+D on) mean %.3fx p95 %.3fx max %.2fx'%(
      (0.5*(onA.astype(float)+onD.astype(float))).mean(),
      (0.5*(onA.astype(float)+onD.astype(float))).quantile(0.95),
      (0.5*(onA.astype(float)+onD.astype(float))).max()))
# turnover per year (cost reality)
pA=pd.Series(np.where(rz(MOM).shift(1)<0.0,1.0,0.0),index=MOM.index).shift(1).reindex(pv.index).fillna(0.0)
pD=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index).shift(1).reindex(pv.index).fillna(0.0)
to=(pA.diff().abs()/2+pD.diff().abs()/2)/2
print('blend one-side turnover/day %.4f => %.1f%%/yr cost at 6bps'%(to.mean(),to.mean()*252*6/1e4*100))
