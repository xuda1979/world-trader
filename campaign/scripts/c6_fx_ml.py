"""C6 Idea 4: FX-cross-ML. 8 FX pairs + gold + rates spreads -> GBM predict 5d DXY sign ->
short USD majors (inverse DXY proxy) basket, vol-normalized. T+1, 6bps, vt 10% trailing."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval
from sklearn.ensemble import GradientBoostingClassifier
import warnings; warnings.filterwarnings('ignore')
FRED='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred'
NEWD='/Users/daxu/software/world-trader/tools/quant/data/newdata'
def lf(n):
    df=pd.read_csv(f'{FRED}/{n}.csv',index_col=0,parse_dates=True); v=df.iloc[:,0].astype(float)
    return v[~v.index.duplicated(keep='last')].dropna()
def ln(n):
    df=pd.read_csv(f'{NEWD}/{n}.csv',index_col=0,parse_dates=True); v=df.iloc[:,0].astype(float)
    return v[~v.index.duplicated(keep='last')].dropna()

dxy = lf('dxy')
pairs = {'eur':lf('eur'),'gbp':lf('gbp'),'jpy':lf('jpy'),'cad':lf('cad')}
pairs['aud']=ln('DEXUSAL'); pairs['chf']=ln('DEXSFUS')
xau = lf('xau'); y2=lf('DGS2'); y10=lf('DGS10'); vix=lf('vix')
P = pd.DataFrame(pairs); P['xau']=xau; P['dxy']=dxy; P['y2']=y2; P['y10']=y10; P['vix']=vix
P=P.sort_index().loc['2006-01-01':]
P=P.ffill(limit=5).dropna()
print('panel',P.index.min().date(),P.index.max().date(),len(P))

F=pd.DataFrame(index=P.index)
for c in ['eur','gbp','jpy','cad','aud','chf']:
    r=P[c].pct_change()
    F[f'{c}_r5']=P[c].pct_change(5); F[f'{c}_r21']=P[c].pct_change(21)
    F[f'{c}_z63']=(P[c]/P[c].rolling(63).mean()-1)
    F[f'{c}_v21']=r.rolling(21).std()
F['xau_r21']=P['xau'].pct_change(21)
F['y2_10_spread']=P['y10']-P['y2']
F['spread_d21']=F['y2_10_spread'].diff(21)
F['vix_z']=(P['vix']/P['vix'].rolling(63).mean()-1)
F['dxy_r5']=P['dxy'].pct_change(5); F['dxy_r21']=P['dxy'].pct_change(21)
y = (P['dxy'].pct_change(5).shift(-5)>0).astype(int)   # 5d fwd DXY up
data=pd.concat([F,y.rename('y')],axis=1).dropna()
X=['eur_r5','eur_r21','eur_z63','eur_v21','gbp_r5','gbp_r21','gbp_z63','gbp_v21',
   'jpy_r5','jpy_r21','jpy_z63','jpy_v21','cad_r5','cad_r21','cad_z63','cad_v21',
   'aud_r5','aud_r21','aud_z63','aud_v21','chf_r5','chf_r21','chf_z63','chf_v21',
   'xau_r21','y2_10_spread','spread_d21','vix_z','dxy_r5','dxy_r21']
dates=data.index
mends=pd.date_range('2008-07-01',dates.max(),freq='ME')
sig=pd.Series(np.nan,index=dates)
for me in mends:
    te=(dates>me)&(dates<=me+pd.offsets.MonthEnd(1)); tr=dates<=me-pd.Timedelta(days=7)
    if tr.sum()<378 or te.sum()==0: continue
    m=GradientBoostingClassifier(n_estimators=80,max_depth=2,learning_rate=0.05,subsample=0.8,random_state=0)
    m.fit(data.loc[tr,X],data.loc[tr,'y'])
    sig.loc[dates[te]]=m.predict_proba(data.loc[te,X])[:,1]-0.5
print('sig coverage',round(sig.notna().mean(),3))
# proxy book: short USD vs 4 majors (inverse DXY), vol-normalized each, equal weight
inv={'eur':1,'gbp':1,'jpy':-1,'chf':1}   # jpy: dxy short = long jpy; jpy quoted as USDJPY so long jpy = +pct of P['jpy']
# USDJPY: P up = USD up. Short USD = -pct. EUR/GBP/CHF: P up = foreign up; short USD = +pct.
w=pd.DataFrame(index=sig.index)
for c,s in {'eur':+1,'gbp':+1,'jpy':-1,'chf':+1}.items():
    r=P[c].pct_change(); v=r.rolling(60).std()*np.sqrt(252)
    w[c]=np.sign(-sig)*s*0.10/v.shift(1)     # short USD when model says DXY down; scale 10% ann per leg
w=w.fillna(0).clip(-3,3)
pnl=pd.DataFrame({c:P[c].pct_change() for c in ['eur','gbp','jpy','chf']})
gross=(w*pnl).sum(axis=1)
turn=w.diff().abs().sum(axis=1).fillna(0)
net=gross-6e-4*turn
net=net[net.index>='2008-01-01']
ns,sc=vol_target(net,0.10)
st=full_stats(ns); h1,h2=halves_sr(ns); pv,rsr=scramble_pval(ns)
print('FULL',{k:(round(v,2) if isinstance(v,float) else v) for k,v in st.items() if k!='yearly'})
print('halves',round(h1,2),round(h2,2),'scramble p',pv,'scale mean',round(sc.mean(),2))
oos=ns[ns.index>='2017-01-01']
print('OOS',{k:(round(v,2) if isinstance(v,float) else v) for k,v in full_stats(oos).items() if k!='yearly'})
b=pd.read_csv('/Users/daxu/software/world-trader/campaign/results/COORD_FINAL_daily.csv',index_col=0,parse_dates=True)['ret']
j=pd.concat([ns,b],axis=1,join='inner').dropna(); print('corr blend',round(j.corr().iloc[0,1],3),'n',len(j))
print('yearly',st['yearly'])
ns.to_frame('ret').to_csv('/tmp/c6_fx_ml.csv')
