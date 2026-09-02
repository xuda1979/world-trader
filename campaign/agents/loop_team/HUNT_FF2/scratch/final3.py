"""FINAL 3: CORRECT position-lag scramble on delivered-file generator (circular shift of
POSITION series, PnL vs real factor returns, costs recomputed), 200 perms x 3 seeds.
This is the charter gate: p<0.05 required. Applied to raw and poolvt variants."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

pv=pd.read_csv('../sleeves/FF2_DUALGATE_poolvt_daily.csv',index_col=0,parse_dates=True)['ret']
raw=pd.read_csv('../sleeves/FF2_DUALGATE_raw_daily.csv',index_col=0,parse_dates=True)['ret']
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()
posA=pd.Series(np.where(rz(MOM).shift(1)<0.0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)

def raw_net(pos,r,lag=None):
    p=pos.shift(1).reindex(r.index)
    if lag is not None:
        p=pd.Series(np.roll(p.fillna(0.0).values,lag),index=r.index)
    net=p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST
    return net.dropna()

def blend(lag=None, vt=True, cap=3.0):
    bl=(raw_net(posA,MOM,lag)+raw_net(posD,MKT,lag)).dropna()
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    if vt:
        sd=bl.rolling(60,min_periods=60).std()*np.sqrt(252)
        bl=bl*((0.08/sd).clip(upper=cap).shift(1).fillna(1.0)).dropna() if False else \
           (bl*((0.08/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()
    return bl

real_vt=blend(vt=True).mean()/blend(vt=True).std()*np.sqrt(252)
real_raw=blend(vt=False).mean()/blend(vt=False).std()*np.sqrt(252)
print('real SR: poolvt %.4f raw %.4f'%(real_vt,real_raw))
for seed in (7,11,23):
    rng=np.random.default_rng(seed); T=len(pv); cnt_v=0; cnt_r=0; n=200
    for _ in range(n):
        lag=int(rng.integers(21,T-21))
        bv=blend(lag=lag,vt=True); br=blend(lag=lag,vt=False)
        if float(bv.std())>0 and float(bv.mean())/float(bv.std())*np.sqrt(252)>=real_vt: cnt_v+=1
        if float(br.std())>0 and float(br.mean())/float(br.std())*np.sqrt(252)>=real_raw: cnt_r+=1
    print(f'seed {seed}: poolvt p={cnt_v/n:.3f}  raw p={cnt_r/n:.3f}')
