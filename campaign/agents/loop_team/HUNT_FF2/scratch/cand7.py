"""CANDIDATE 7: VIX 2-source check (alphaportfolio vs FRED VIXCLS) + sleeve rebuild on FRED VIX.
Also the residual path check: is the 'vol-gate' just a conditional-beta story?"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

ap=lib.load_vix()
fr=pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/VIXCLS.csv',
               index_col=0,parse_dates=True)['VIXCLS']
fr=pd.to_numeric(fr,errors='coerce').dropna()
fr=fr[~fr.index.duplicated(keep='last')]
j=pd.concat([ap.rename('ap'),fr.rename('fred')],axis=1,join='inner').dropna()
j=j[j.index>=pd.Timestamp('2008-01-01')]
d=(j['ap']-j['fred']).abs()
print(f"VIX 2-source: n={len(j)} corr={j['ap'].corr(j['fred']):.5f} max|diff|={d.max():.3f} mean|diff|={d.mean():.4f} days diff>0.5: {(d>0.5).sum()}")

# rebuild sleeve on FRED VIX
ff=lib.load_ff3(); mom=lib.load_mom()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    return (p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST).dropna()
def poolvt(r,tgt=0.08,cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (r*((tgt/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()
Vf=fr.reindex(MKT.index).ffill()
zvf=(Vf-Vf.rolling(252).mean())/Vf.rolling(252).std()
posAf=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index)
posDf=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zvf.shift(1)<0.0),1.0,0.0),index=MKT.index)
blf=poolvt(((raw_net(posAf,MOM)+raw_net(posDf,MKT))/2)[lambda s:s.index>=pd.Timestamp('2008-01-01')])
print('FRED-VIX rebuild: SR %.3f (AP-VIX was 1.080)'%(blf.mean()/blf.std()*np.sqrt(252)))
sr_=pd.read_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
jj=pd.concat([blf.rename('fred'),sr_.rename('ap')],axis=1,join='inner').dropna()
print('corr(fred rebuild, delivered file) = %.4f'%jj['fred'].corr(jj['ap']))
