"""CANDIDATE 8: T+1 audit + perturbation causality (the campaign's causality probes):
(a) shift the SIGNAL one extra day (should degrade, not break -> signal is causal)
(b) REVERSE the signal (SR should flip/negate -> edge is in the signal, not the mechanics)
(c) VIX z uses same-day VIX vs next-day: verify no same-day PnL: pos decided on t's close,
    PnL t->t+1. FF factor daily data are daily returns for day t (CRSP convention) so a pos
    decided with rz(t) earns r(t+1). shift chain: z uses data<=t; pos.shift(1)*r => pos(t) earns r(t+1). OK.
(d) same-day leak probe: build pos WITHOUT shift(1) in net (i.e., pos(t)*r(t)) -> if SR explodes,
    the original is causally OK.
(e) bootstrap on signal date: replace rz win 63 with win 62 (irrelevant change) -> SR stability.
"""
import sys; sys.path.insert(0,'.')
import lib, numpy as np, pandas as pd

ff=lib.load_ff3(); mom=lib.load_mom(); vix=lib.load_vix()
def rz(s, win=63, minp=40):
    rv=s.rolling(win,min_periods=minp).std()
    return (rv-rv.expanding(252).mean())/rv.expanding(252).std()
MOM=mom['MOM'][mom['MOM'].index>='2005-01-01']
MKT=ff['Mkt-RF'][ff['Mkt-RF'].index>='2005-01-01']
V=vix.reindex(MKT.index).ffill()
zv=(V-V.rolling(252).mean())/V.rolling(252).std()

def build(extra_shift=0, invert=False, leak=False, win=63):
    zA=rz(MOM,win).shift(extra_shift)
    zD=rz(MKT,win).shift(extra_shift)
    zv2=zv.shift(extra_shift)
    posA=pd.Series(np.where(zA.shift(1)<0,1.0,0.0),index=MOM.index)
    posD=pd.Series(np.where((zD.shift(1)<0.5)&(zv2.shift(1)<0.0),1.0,0.0),index=MKT.index)
    if invert:
        posA=1-posA; posD=1-posD
    pA=posA.shift(0 if leak else 1).reindex(MOM.index)
    pD=posD.shift(0 if leak else 1).reindex(MKT.index)
    netA=pA*MOM-(pA.diff().abs()/2.0).fillna(0.0)*lib.COST
    netD=pD*MKT-(pD.diff().abs()/2.0).fillna(0.0)*lib.COST
    bl=((netA+netD)/2).dropna()
    bl=bl[bl.index>=pd.Timestamp('2008-01-01')]
    sd=bl.rolling(60,min_periods=60).std()*np.sqrt(252)
    return (bl*((0.08/sd).clip(upper=3.0).shift(1).fillna(1.0))).dropna()
for tag,kw in [('BASE',{}),('signal+1d',{ 'extra_shift':1}),('signal+2d',{'extra_shift':2}),
               ('INVERTED',{'invert':True}),('LEAK(same-day)',{'leak':True}),('win62',{'win':62})]:
    x=build(**kw)
    print(f"{tag:14s}: SR {x.mean()/x.std()*np.sqrt(252):+.3f}")
