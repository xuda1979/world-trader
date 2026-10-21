"""RECON 9 (decontaminated): full-sample blend table. A/B/D/F via net_of (Series),
C via net_of_book (DataFrame, fillna(0) both sides -> no NaN-row loss)."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob, itertools

champ=lib.load_champion()
def build(pos,r):
    if isinstance(pos,pd.DataFrame): net=lib.net_of_book(pos,r)
    else: net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    return net[net.index>=pd.Timestamp('2008-01-01')].dropna()

ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

names={}
names['A']=build(pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index),MOM)
names['B']=build(pd.Series(np.where(rz(MKT).shift(1)<0.5,1.0,0.0),index=MKT.index),MKT)
zg=(rz(MKT)<0.5)&(zv.shift(1)<0.0)
names['D']=build(pd.Series(np.where(zg,1.0,0.0),index=MKT.index),MKT)
px={}
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]; px[n]=pd.read_csv(f,index_col=0,parse_dates=True)['close']
P=pd.DataFrame(px); R=P.pct_change(); Rm=R.mask(R.abs()>0.25)
v=Rm.rolling(25,min_periods=10).std(); q=v.rank(axis=1,pct=True)
w=(q<=0.5).astype(float)*(1.0/v)
w=w.div(w.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
names['C']=build(w,Rm)
names['F']=build(np.sign(MOM.rolling(252).sum()),MOM)

print('lens:',{k:len(x) for k,x in names.items()})
print('single SRs:',{k:round(x.mean()/x.std()*np.sqrt(252),3) for k,x in names.items()})
J=pd.DataFrame(names).dropna()
print('J rows:',len(J))
print('corr:\n',J.corr().round(3))
def rep(tag,bl):
    st=lib.full_stats(bl); h1,h2=lib.halves_sr(bl)
    okn,ny=lib.negyr_tol(bl); corr,_=lib.corr_to(bl,champ); fg=lib.flatten_gates(bl)
    okg=(st['sr']>=0.6 and h1>=0.3 and h2>=0.3 and okn and abs(corr)<0.15 and fg['ac1']<0.5 and fg['uniqR']>=0.08)
    print(f"{tag}: SR {st['sr']:.2f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
          f"H1 {h1:.2f} H2 {h2:.2f} corr {corr:+.3f} ac1 {fg['ac1']:.2f} uniqR {fg['uniqR']:.2f} {'<<< ALL-GATES' if okg else ''}")
for r in (2,3):
    for c in itertools.combinations(names.keys(),r):
        bl=J[list(c)].sum(axis=1)/r
        rep('+'.join(c),bl)
# vol-scaled variant of best pair: scale each sleeve to 10% vol trailing before blend
def vt10(x):
    rv=x.expanding(60).std()*np.sqrt(252)
    return x*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
Jv=pd.DataFrame({k:vt10(x) for k,x in names.items()}).dropna()
for c in [('A','C'),('A','F'),('A','C','F'),('D','F'),('A','D','F')]:
    bl=Jv[list(c)].sum(axis=1)/len(c)
    rep('VT10 '+'+'.join(c),bl)
