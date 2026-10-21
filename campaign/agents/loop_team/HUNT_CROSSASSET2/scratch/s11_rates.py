"""FAMILY 2: RATES-CURVE steepener momentum (2s10s, 5s30s etc). Paper screen on yield spreads,
then REAL-ETF DV01 variants (TLT/IEF/AGG). Distinctness check vs C2_steep_carry corr later."""
import sys; sys.path.insert(0,'.')
from lib import *
import itertools
Y={f:fred(f) for f in ['DGS1','DGS2','DGS5','DGS7','DGS10','DGS20','DGS30']}
Y=pd.DataFrame(Y).loc['2000':]
blend=load_blend()
spreads={'2s10':Y.DGS10-Y.DGS2,'5s30':Y.DGS30-Y.DGS5,'2s5':Y.DGS5-Y.DGS2,'5s10':Y.DGS10-Y.DGS5,
         '10s30':Y.DGS30-Y.DGS10,'7s20':Y.DGS20-Y.DGS7,'1s10':Y.DGS10-Y.DGS1}
rows=[]
for nm,sp in spreads.items():
    sp08=sp.dropna(); sp08=sp08[sp08.index>='2008-01-01']
    for lb in [10,21,42,63,126,252]:
        for mode in ['mom','rev']:
            sig=np.sign(sp-sp.shift(lb)); pos=sig if mode=='mom' else -sig
            r,pos_=net_of(pos,sp.diff())
            r2=r[r.index>='2008-01-01']
            if len(r2)<3000: continue
            st=full_stats(r2)
            j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
            corr=j.s.corr(j.c)
            rows.append(dict(spread=nm,mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],
                             negy=st['negy'],worst=st['worst'],corr=corr,n=len(r2)))
res=pd.DataFrame(rows).sort_values('sr',ascending=False)
res.to_csv('s11_rates_results.csv',index=False)
print(res.to_string())
# REAL-ETF DV01 steepener: IEF(7-10y) vs TLT(20y), DV01-neutral (d_TLT=17, d_IEF=7.5): n_IEF/n_TLT=17/7.5
pxT=load_csv(f'{ROOT}/tools/quant/data/twelvedata/TLT.csv').pct_change()
pxI=load_csv(f'{ROOT}/tools/quant/data/twelvedata/IEF.csv').pct_change()
pxA=load_csv(f'{ROOT}/tools/quant/data/twelvedata/AGG.csv').pct_change()
dv=pd.DataFrame({'ieftlt':17/7.5*pxI-pxT,'aggie':7.5/6.0*pxI-pxA if False else 1.25*pxA-pxI}).loc['2007':]
print('--- real-ETF DV01 books, own momentum lb ---')
rows2=[]
for nm,br in dv.items():
    br08=br.dropna(); br08=br08[br08.index>='2008-01-01']
    for lb in [10,21,42,63,126,252]:
        for mode in ['mom','rev']:
            lvl=pd.Series(1.0,index=br.index)  # book level via cumsum proxy not needed; momentum on book ret sum
            sig=np.sign(br.rolling(lb).sum())
            pos=sig if mode=='mom' else -sig
            r,pos_=net_of(pos,br)
            r2=r[r.index>='2008-01-01']
            st=full_stats(r2)
            j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
            rows2.append(dict(book=nm,mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],negy=st['negy'],worst=st['worst'],corr=j.s.corr(j.c)))
print(pd.DataFrame(rows2).sort_values('sr',ascending=False).to_string())
