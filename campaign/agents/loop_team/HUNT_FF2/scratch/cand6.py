"""CANDIDATE 6: honesty stress on the A vs D composition. Questions:
(1) How much of A+D is just MKT beta exposure (raw MKT long when on)? corr to MKT and SMB/HML betas.
(2) A-only and D-only pools vs blend: is the blend redundant with a SINGLE simple gate?
(3) Correlation of the blend to each committed champion sleeve family (dualmom? brwt15? CFX4?)
    — proxy check: corr to champion (done), corr to MKT (market), corr to 2008+ MOM factor.
(4) OOS convention: arithmetic OOS17+ for the poolvt file.
(5) VIX data integrity: alphaportfolio vix_daily vs FRED VIXCLS (2nd source) — corr + max diff."""
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
zv=(V-V.rolling(252).mean())/V.rolling(252).std()
def raw_net(pos,r):
    p=pos.shift(1).reindex(r.index)
    return (p*r-(p.diff().abs()/2.0).fillna(0.0)*lib.COST-lib.BORROW*p.clip(upper=0.0).abs()).dropna()
def poolvt(r, tgt=0.08, cap=3.0):
    sd=r.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (r*((tgt/sd).clip(upper=cap).shift(1).fillna(1.0))).dropna()
posA=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index)
posD=pd.Series(np.where((rz(MKT).shift(1)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index)
bl=poolvt(((raw_net(posA,MOM)+raw_net(posD,MKT))/2)[lambda s: s.index>=pd.Timestamp('2008-01-01')])

# (1)(3) betas
J=pd.concat([bl.rename('sleeve'),ff['Mkt-RF'].rename('MKT'),ff['SMB'].rename('SMB'),
             ff['HML'].rename('HML'),mom['MOM'].rename('MOM')],axis=1,join='inner').dropna()
J=J[J.index>=pd.Timestamp('2008-01-01')]
import numpy.linalg as la
X=J[['MKT','SMB','HML','MOM']].values
X=np.column_stack([np.ones(len(X)),X])
y=J['sleeve'].values
beta,res,rank,sv=la.lstsq(X,y,rcond=None)
pred=X@beta
resid=y-pred
print('FF4 betas: alpha_d %.2e alpha_ann %.2f%% beta_MKT %.3f SMB %.3f HML %.3f MOM %.3f'%(
    beta[0],beta[0]*252*100,beta[1],beta[2],beta[3],beta[4]))
print('resid SR: %.3f (raw SR %.3f); corr sleeve-MKT %.3f'%(resid.mean()/resid.std()*np.sqrt(252),
      bl.mean()/bl.std()*np.sqrt(252), J['sleeve'].corr(J['MKT'])))
r2=1-resid.var()/y.var()
print('R2 %.3f'%r2)

# (2) singles vs blend (poolvt)
A=poolvt(raw_net(posA,MOM)[lambda s:s.index>=pd.Timestamp('2008-01-01')])
D=poolvt(raw_net(posD,MKT)[lambda s:s.index>=pd.Timestamp('2008-01-01')])
for tag,s in [('A',A),('D',D),('A+D',bl)]:
    st=lib.full_stats(s); print(f"{tag}: SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']}")

# (4) OOS17+ arithmetic
oos=bl[bl.index>=pd.Timestamp('2017-01-01')]
print('OOS17+ (arith ann): %.1f%%'%(oos.mean()*252*100))
print('OOS17+ (geo ann): %.1f%%'%(((1+oos).prod())**(252/len(oos))-1)*1 if False else 'OOS17+ geo %.1f%%'%(((1+oos).prod())**(252/len(oos))-1)*100)
# (5) VIX 2nd source
fr=pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/VIXCLS.csv')
print('FRED VIXCLS cols:',fr.columns.tolist()[:3])
