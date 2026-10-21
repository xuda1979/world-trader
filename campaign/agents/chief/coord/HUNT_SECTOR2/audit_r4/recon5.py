"""RECON 5: year-by-year of the 3 leading cells + pairwise corr + blend search."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd, glob

champ=lib.load_champion()
def build(pos,r):
    if isinstance(pos,pd.DataFrame): net=lib.net_of_book(pos,r)
    else: net,_=lib.net_of(pos,r)
    rv=net.expanding(60).std()*np.sqrt(252)
    net=net*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    return net[net.index>=pd.Timestamp('2008-01-01')].dropna()

# sleeve A: vm_MOM_rv63_z0.0
ff=lib.load_ff3(); mom=lib.load_mom()
MOM=mom['MOM']; MOM=MOM[MOM.index>='2005-01-01']
rv63=MOM.rolling(63,min_periods=40).std()
z=(rv63-rv63.expanding(252).mean())/rv63.expanding(252).std()
posA=pd.Series(np.where(z.shift(1)<0.0,1.0,0.0),index=MOM.index)
A=build(posA,MOM)
# sleeve B: vm_MKT_rv63_z0.5
MKT=ff['Mkt-RF']; MKT=MKT[MKT.index>='2005-01-01']
rv63b=MKT.rolling(63,min_periods=40).std()
zb=(rv63b-rv63b.expanding(252).mean())/rv63b.expanding(252).std()
posB=pd.Series(np.where(zb.shift(1)<0.5,1.0,0.0),index=MKT.index)
B=build(posB,MKT)
# sleeve C: BAB invvol long-only half
px={}
for f in sorted(glob.glob('/Users/daxu/software/world-trader/tools/quant/data/twelve_big/*.csv')):
    n=f.split('/')[-1][:-4]; px[n]=pd.read_csv(f,index_col=0,parse_dates=True)['close']
P=pd.DataFrame(px); R=P.pct_change(); Rm=R.mask(R.abs()>0.25)
v=Rm.rolling(25,min_periods=10).std(); q=v.rank(axis=1,pct=True)
m=(q<=0.5).astype(float)*(1.0/v)
w=m.div(m.abs().sum(axis=1).replace(0,np.nan),axis=0).fillna(0)
C=build(w,Rm)

names={'A_vmMOMz0':A,'B_vmMKTz0.5':B,'C_BABlong':C}
J=pd.DataFrame(names).dropna()
print('pairwise corr:\n',J.corr().round(3))
for nm,s in names.items():
    x=s.dropna(); st=lib.full_stats(x)
    yr=x.groupby(x.index.year).apply(lambda g:(1+g).prod()-1)
    print(f"\n{nm}: SR {st['sr']:.2f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']}")
    print('  ',{int(k):f'{v_:+.1%}' for k,v_ in yr.items()})

# blend grid: A+B, A+C, A+B+C equal weight (50/50 of vol-normalized already)
import itertools
def blend(sr_):
    Jd=pd.DataFrame({k:names[k] for k in sr_}).dropna()
    n=len(sr_)
    bl=Jd.sum(axis=1)/n
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    st=lib.full_stats(bl); h1,h2=lib.halves_sr(bl)
    okn,ny=lib.negyr_tol(bl); corr,_=lib.corr_to(bl,champ)
    fg=lib.flatten_gates(bl)
    print(f"blend {sr_}: SR {st['sr']:.2f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} negy {st['negy']} worst {st['worst']:+.1%} "
          f"H1 {h1:.2f} H2 {h2:.2f} corr {corr:+.3f} ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f}")
    return bl
combos=[('A_vmMOMz0','B_vmMKTz0.5'),('A_vmMOMz0','C_BABlong'),('B_vmMKTz0.5','C_BABlong'),
        ('A_vmMOMz0','B_vmMKTz0.5','C_BABlong')]
best=None
for c in combos:
    bl=blend(c)
