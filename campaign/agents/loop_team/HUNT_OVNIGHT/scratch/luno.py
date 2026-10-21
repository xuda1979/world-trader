"""FINAL DECISION DATA: LUNO gate on OVNCAP126k25:
paper SR 2.145 (implied ON-per-day 23.4bp) vs LUNO eq ann 13.7% (daily 5.44bp) => haircut 77%.
Also: 12m rolling window SR>0 frac; max subwindow SR; drawdown of vt series; OOS17 geo; 
final deliverable = NEGATIVE result unless LUNO passes (it won't)."""
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
sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
netv=(net*sc).dropna(); n08=netv[netv.index>='2008-01-01']

# implied daily edge
gross_daily=n08.mean()
print(f'implied paper edge: {gross_daily*1e4:.2f} bp/day')
luno_daily=0.137/252
print(f'LUNO tradable edge: {luno_daily*1e4:.2f} bp/day -> haircut {100*(1-luno_daily/gross_daily):.0f}%')

# rolling 12m SR
roll=n08.rolling(252).apply(lambda x: x.mean()/x.std()*np.sqrt(252) if x.std()>0 else 0)
print(f'12m rolling SR: min {roll.min():.2f} p10 {roll.quantile(.1):.2f} frac>0 {float((roll>0).mean()):.2f}')
roll_m=roll.rolling(21).mean()
print(f'21d-smoothed rolling SR: min {roll_m.min():.2f}, frac days <0.5: {float((roll_m<0.5).mean()):.2f}')
# max subwindow SR over 1y windows
srs=[]
for i in range(0,len(n08)-252,21):
    w=n08.iloc[i:i+252]; srs.append(w.mean()/w.std()*np.sqrt(252))
srs=np.array(srs)
print(f'1y window SR: mean {srs.mean():.2f} min {srs.min():.2f} max {srs.max():.2f} frac>1: {(srs>1).mean():.2f}')
# drawdown of vt series
eq=(1+n08).cumprod()
dd=(eq/eq.cummax()-1)
print(f'maxDD vt: {dd.min()*100:.1f}%')
# OOS17 geo
o=n08[n08.index>='2017-01-01']
print(f'OOS17+ geo ann {((1+o).prod()**(252/len(o))-1)*100:.1f}%')
