"""FAMILY 1: SECTOR-BASKET relative momentum on REAL ETF prices (twelvedata).
Pairs among sectors {XLE,XLB,XLF,XLI} + sector/macro relatives (vs GLD, IEF, TLT, QQQ, AGG).
Signal: sign(momentum of spread) lb in {10,21,42,63,126,252} and REVERSE. T+1, 6.4bps/side."""
import sys; sys.path.insert(0,'.')
from lib import *
import itertools, os
TICK=['XLE','XLB','XLF','XLI','GLD','IEF','TLT','QQQ','AGG','SPY']
px={t:load_csv(f'{ROOT}/tools/quant/data/twelvedata/{t}.csv') for t in TICK}
rets={t:px[t].pct_change() for t in TICK}
DF=pd.DataFrame(rets).loc['2007-06':]
blend=load_blend()
rows=[]
pairs=[(a,b) for a,b in itertools.combinations(['XLE','XLB','XLF','XLI'],2)]
rel=[('XLE','GLD'),('XLE','TLT'),('XLB','GLD'),('XLF','IEF'),('XLI','GLD'),('XLF','XLE'),
     ('XLE','QQQ'),('XLF','QQQ'),('XLI','QQQ'),('QQQ','IEF'),('SPY','IEF'),('XLE','AGG')]
def spread_r(a,b):
    return (DF[a]-DF[b]).dropna()
for a,b in pairs+rel:
    sr_=spread_r(a,b); sr08=sr_[sr_.index>='2008-01-01']
    if len(sr08)<3000: continue
    for lb in [10,21,42,63,126,252]:
        spread_px=(px[a]/px[b]).reindex(sr_.index).ffill()
        for mode in ['mom','rev']:
            sig=np.sign(spread_px-spread_px.shift(lb))
            pos=sig if mode=='mom' else -sig
            r,pos_=net_of(pos,sr_)
            r2=r[r.index>='2008-01-01']
            if len(r2)<3000: continue
            st=full_stats(r2)
            j=pd.concat([r2.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
            corr=j.s.corr(j.c)
            h1,h2=halves_sr(r2)
            rows.append(dict(pair=f'{a}-{b}',mode=mode,lb=lb,sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],
                             negy=st['negy'],worst=st['worst'],h1=h1,h2=h2,corr=corr,n=len(r2)))
res=pd.DataFrame(rows).sort_values('sr',ascending=False)
res.to_csv('s10_sector_results.csv',index=False)
print(res.head(30).to_string())
print('...total',len(res))
