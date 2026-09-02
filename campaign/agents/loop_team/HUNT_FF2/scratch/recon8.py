"""RECON 8: avg-verdict + blend refinement of best cells. Candidates:
A=vm_MOM_rv63_z0 (SR .69), D=MKT dual th_r0.5 th_v0 (SR .78), B=vm_MKT_z0.5 (SR .68),
C=BAB long half (SR .58), E=vm_SMB? no. F=tcmom MOM 252 LS (SR .62).
Test ALL pairwise + triple blends of top-5 with SR + gates."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob, itertools

champ=lib.load_champion()
def build(pos,r):
    net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    if isinstance(net,pd.DataFrame): net=net.sum(axis=1)
    net=net[net.index>=pd.Timestamp('2008-01-01')].dropna()
    return net
def stats(net):
    st=lib.full_stats(net); h1,h2=lib.halves_sr(net)
    okn,ny=lib.negyr_tol(net); corr,_=lib.corr_to(net,champ); fg=lib.flatten_gates(net)
    return dict(sr=st['sr'],ann=st['ann_geo'],mdd=st['mdd'],negy=st['negy'],worst=st['worst'],
                h1=h1,h2=h2,corr=corr,ac1=fg['ac1'],uniq=fg['uniqR'],n=st['n'])

ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

names={}
# A: MOM rv-z<0
pos=pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index); names['A']=build(pos,MOM)
# B: MKT rv-z<0.5
pos=pd.Series(np.where(rz(MKT).shift(1)<0.5,1.0,0.0),index=MKT.index); names['B']=build(pos,MKT)
# D: MKT dual rv<0.5 vix-z<0
zg=(rz(MKT)<0.5)&(zv.shift(1)<0.0)
names['D']=build(pd.Series(np.where(zg,1.0,0.0),index=MKT.index),MKT)
# C: BAB long half
px={}
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]; px[n]=pd.read_csv(f,index_col=0,parse_dates=True)['close']
P=pd.DataFrame(px); R=P.pct_change(); Rm=R.mask(R.abs()>0.25)
v=Rm.rolling(25,min_periods=10).std(); q=v.rank(axis=1,pct=True)
w=(q<=0.5).astype(float)*(1.0/v)
w=w.div(w.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
names['C']=build(w,Rm)
# F: tcmom MOM 252 LS
s=MOM
pos=np.sign(s.rolling(252).sum())
names['F']=build(pos,s)

print('single-cell SRs:', {k:round(v.mean()/v.std()*np.sqrt(252),3) for k,v in names.items()})
print()
J=pd.DataFrame(names).dropna()
print('corr matrix:\n',J.corr().round(3))
print()
for r in (2,3):
    for c in itertools.combinations(names.keys(),r):
        bl=J[list(c)].sum(axis=1)/r
        bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
        st=stats(bl)
        okneg,_=lib.negyr_tol(bl)
        okg=(st['sr']>=0.6 and st['h1']>=0.3 and st['h2']>=0.3 and okneg and abs(st['corr'])<0.15
             and st['ac1']<0.5 and st['uniq']>=0.08)
        print(f"blend {'+'.join(c)}: SR {st['sr']:.2f} ann {st['ann']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
              f"H1 {st['h1']:.2f} H2 {st['h2']:.2f} corr {st['corr']:+.3f} ac1 {st['ac1']:.2f} uniqR {st['uniq']:.2f} {'<<< GATES' if okg else ''}")
