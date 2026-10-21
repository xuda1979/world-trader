"""FIX to charter trade schedule while keeping decomposition as TARGET: hold the book through
the day (close_t -> close_{t+1} position), and REBALANCE to keep longs' ON premium? No such thing.
Instead: the ONLY tradeable structure at 6.4bps/side that can harvest ON premium is one that
buys at close and sells at NEXT close (cc). Any ON-only earning needs a daily exit at open.
Test the 0.35 cap3 VT variant of OVNCAP as a DISCLOSED PAPER construct anyway, plus:
1. weekly rebalance OVNCAP (turnover collapses; is edge weekly-persistent?)
2. sparse trade: hold only days with high signal conviction
3. pragmatic blend: OVNCAP at 0.35 cap3 = ann ~13%, corr to champ?
"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=H.xs_ls(sig,k=k)
p=pos.shift(1).fillna(0.0)
r1=on.fillna(0.0); r2=ic.fillna(0.0)
turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
net=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor).dropna()
rv=net.expanding(60).std()*np.sqrt(252)
sc=(0.35/rv).clip(upper=3.0).shift(1).fillna(1.0)
netv=(net*sc).dropna(); n08=netv[netv.index>='2008-01-01']
champ=H.load_champion()
st=H.full_stats(n08); corr,nc=H.corr_to(n08,champ)
print(f'OVNCAP vt0.35cap3: SR {st["sr"]:.3f} ann {st["ann_geo"]*100:+.1f}% MDD {st["mdd"]*100:.1f}% corr {corr:+.3f}(n={nc})')

print()
print('=== weekly rebalance (positions frozen to Monday) ===')
posw=pos.copy()
# freeze: only allow position changes on first trading day of ISO week
dow=pd.Series(pos.index.dayofweek,index=pos.index)
freeze=dow.ne(dow.shift(1))|pd.Series(pos.index.isocalendar().week.values,index=pos.index).ne(pd.Series(pos.index.isocalendar().week.values,index=pos.index).shift(1))
posw[~freeze]=np.nan
posw=posw.ffill().fillna(0.0)
pw=posw.shift(1).fillna(0.0)
turnw=(pw.diff().abs().sum(axis=1)/2.0).fillna(0.0)
netw=(pw.mul(r1).sum(axis=1)-pw.mul(r2).sum(axis=1)-turnw*H.COST-bor).dropna()
rvw=netw.expanding(60).std()*np.sqrt(252); scw=(0.10/rvw).clip(upper=3.0).shift(1).fillna(1.0)
nw=(netw*scw).dropna(); nw08=nw[nw.index>='2008-01-01']
stw=H.full_stats(nw08); corrw,ncw=H.corr_to(nw08,champ)
print(f'OVNCAP weekly-rebal vt.10: SR {stw["sr"]:.3f} ann {stw["ann_geo"]*100:+.1f}% MDD {stw["mdd"]*100:.1f}% corr {corrw:+.3f} | turnover {turnw[turnw.index>="2008-01-01"].mean()*1e4:.1f}bp/day')
h1,h2=H.halves_sr(nw08)
print(f'   H1 {h1:.2f} H2 {h2:.2f} negy {stw["negy"]}/{stw["years"]} worst {stw["worst"]*100:+.1f}% ac1 {H.flatten_gates(nw08)["ac1"]:.3f} uniqR {H.flatten_gates(nw08)["uniqR"]:.3f}')
pv,rl=H.position_lag_p2(posw,on,ic,n=200,seed=0)
print(f'   poslag2_p {pv:.3f}')

print()
print('=== monthly rebalance ===')
posm=pos.copy()
mid=pd.Series(pos.index.month,index=pos.index)
f2=mid.ne(mid.shift(1))
posm[~f2]=np.nan; posm=posm.ffill().fillna(0.0)
pm=posm.shift(1).fillna(0.0)
turnm=(pm.diff().abs().sum(axis=1)/2.0).fillna(0.0)
netm=(pm.mul(r1).sum(axis=1)-pm.mul(r2).sum(axis=1)-turnm*H.COST-bor).dropna()
rvm=netm.expanding(60).std()*np.sqrt(252); scm=(0.10/rvm).clip(upper=3.0).shift(1).fillna(1.0)
nm=(netm*scm).dropna(); nm08=nm[nm.index>='2008-01-01']
stm=H.full_stats(nm08); corrm,ncm=H.corr_to(nm08,champ)
print(f'OVNCAP monthly-rebal vt.10: SR {stm["sr"]:.3f} ann {stm["ann_geo"]*100:+.1f}% MDD {stm["mdd"]*100:.1f}% corr {corrm:+.3f} | turnover {turnm[turnm.index>="2008-01-01"].mean()*1e4:.1f}bp/day')
pv2,rl2=H.position_lag_p2(posm,on,ic,n=200,seed=0)
print(f'   poslag2_p {pv2:.3f} | H1 {H.halves_sr(nm08)[0]:.2f} H2 {H.halves_sr(nm08)[1]:.2f}')
