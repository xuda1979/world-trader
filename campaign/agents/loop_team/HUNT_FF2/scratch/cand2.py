"""CANDIDATE 2: A+B vs A+D head-to-head on IDENTICAL span (trim both to common index
ending 2026-06-30, the FF daily data end) + corr to champion trimmed to same end +
scramble on both. Also try A+B and A+D with B/D sharing the exact same index."""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

champ=lib.load_champion()
ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63):
    rv=s.rolling(win,min_periods=40).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

import lib as L
def mk(pos,r):
    p=pos.shift(1).reindex(r.index)
    gross=p*r
    turn=(p.diff().abs()/2.0).fillna(0.0)
    bor=L.BORROW*p.clip(upper=0.0).abs()
    raw=gross-turn*L.COST-bor
    rv=raw.expanding(60).std()*np.sqrt(252)
    net=raw*((0.10/rv).clip(upper=3.0).shift(1).fillna(1.0))
    net=net[net.index>=pd.Timestamp('2008-01-01')]
    return net.dropna()

A=mk(pd.Series(np.where(rz(MOM).shift(1)<0,1.0,0.0),index=MOM.index),MOM)
B=mk(pd.Series(np.where(rz(MKT).shift(1)<0.5,1.0,0.0),index=MKT.index),MKT)
D=mk(pd.Series(np.where((rz(MKT)<0.5)&(zv.shift(1)<0.0),1.0,0.0),index=MKT.index),MKT)
C=mk(pd.Series(np.where(zv.shift(1)<0.0,1.0,0.0),index=MKT.index),MKT)  # VIX-only gate on MKT

def audit(tag,bl,end=None):
    if end: bl=bl[bl.index<=end]
    st=lib.full_stats(bl); h1,h2=lib.halves_sr(bl)
    okn,ny=lib.negyr_tol(bl); corr,nco=lib.corr_to(bl,champ); fg=lib.flatten_gates(bl)
    print(f"{tag}: n={st['n']} span {st['first']}..{st['last']} SR {st['sr']:.3f} ann {st['ann_geo']:.1%} MDD {st['mdd']:.1%} "
          f"negy {st['negy']} worst {st['worst']:+.1%} H1 {h1:.2f} H2 {h2:.2f} corr {corr:+.3f}(n={nco}) "
          f"ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f}")
    return bl

J=pd.concat({'A':A,'B':B,'D':D,'C':C},axis=1).dropna()
print('common rows:',len(J),'span',J.index.min().date(),J.index.max().date())
END='2026-06-30'
ab=audit('A+B full-span ',J['A']+J['B'])
ad=audit('A+D full-span ',J['A']+J['D'])
print()
# corr to champion on matched end (data-end fairness note): champion trimmed to <=2026-06-30
ch2=champ[champ.index<=pd.Timestamp(END)]
print('champ trimmed:',ch2.index.min().date(),ch2.index.max().date(),len(ch2))
for tag,s in [('A+B',J['A']+J['B']),('A+D',J['A']+J['D']),('A',J['A']),('B',J['B']),('D',J['D']),('C_vixonly',J['C'])]:
    c,n=lib.corr_to(s,ch2)
    print(f'corr({tag},champ<=0630) = {c:+.4f} (n={n})')
print()
yr=(J['A']+J['B']).groupby((J['A']+J['B']).index.year).apply(lambda g:(1+g).prod()-1)
print('A+B yearly:',{int(k):f'{v:+.1%}' for k,v in yr.items()})
yr=(J['A']+J['D']).groupby((J['A']+J['D']).index.year).apply(lambda g:(1+g).prod()-1)
print('A+D yearly:',{int(k):f'{v:+.1%}' for k,v in yr.items()})
