"""Pre-delivery scrutiny of OVNCAP126.25 (chosen): 
1. 3 seeds x scramble (seed sensitivity)
2. yearly table + 2008/2009 detail
3. cost stress 10/15/25bps
4. monthly SR + OOS17 arithmetic
5. turnover/borrow actuals + gross-exposure profile
6. 2008 monthly path
7. corr to champion alternate windows (2008+, 2017+)
8. LOYO (leave-one-year-out): SR excluding each year
9. scrub10: drop 10 worst days
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
sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
netv=(net*sc).dropna()
netv08=netv[netv.index>='2008-01-01']

print('1) scramble seeds:')
for sd in [0,1,2]:
    pv,rl=H.position_lag_p2(pos,on,ic,n=200,seed=sd)
    print(f'   seed {sd}: p={pv:.3f} realSR {rl:.3f}')

print('2) yearly (net, vt):')
yr=netv08.groupby(netv08.index.year).apply(lambda x:(1+x).prod()-1)
print('  ', {int(a):round(float(b)*100,1) for a,b in yr.items()})
print('   2008 monthly:', {int(m):round(float(v)*100,1) for m,v in (netv08['2008'].groupby(netv08['2008'].index.month).apply(lambda x:(1+x).prod()-1)*100).items()})
print('   2009 monthly:', {int(m):round(float(v)*100,1) for m,v in (netv08['2009'].groupby(netv08['2009'].index.month).apply(lambda x:(1+x).prod()-1)*100).items()})

print('3) cost stress (naive SR 2008+, vt):')
for cb in [6.4,10,15,25]:
    c=cb/1e4
    n2=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*c-bor).dropna()
    n2=(n2*(0.10/n2.expanding(60).std()*np.sqrt(252)).clip(upper=3.0).shift(1).fillna(1.0)).dropna()
    n2=n2[n2.index>='2008-01-01']
    print(f'   {cb}bps/side: SR {n2.mean()/n2.std()*np.sqrt(252):.3f}')

print('4) monthly-SR & OOS17:')
mm=netv08.groupby(netv08.index.to_period('M')).apply(lambda x:(1+x).prod()-1)
print(f'   SR_monthly {mm.mean()/mm.std()*np.sqrt(12):.3f} (n={len(mm)} months)')
oos=netv08[netv08.index>='2017-01-01']
print(f'   OOS17+ ann(arith) {oos.mean()*252*100:.1f}% SR {oos.mean()/oos.std()*np.sqrt(252):.3f}')

print('5) turnover/borrow/exposure:')
print(f'   mean one-side turnover/day {turn.mean():.4f} ({turn.mean()*1e4:.1f}bp) | cost drag {turn.mean()*6.4:.2f}bp/day')
print(f'   mean gross exposure |pos| sum {p.abs().sum(axis=1).mean():.3f} (target ~0.88: 2*25/mean valid ~56)')
print(f'   borrow drag mean {bor.mean()*1e4:.3f}bp/day; vt scale mean {sc.mean():.2f} p95 {sc.quantile(.95):.2f} max {sc.max():.2f}')

champ=H.load_champion()
j=pd.concat([netv08.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
print(f'7) corr champ full-join {j["s"].corr(j["c"]):+.4f} (n={len(j)}) | 2017+: {j[j.index>="2017-01-01"]["s"].corr(j[j.index>="2017-01-01"]["c"]):+.4f}')

print('8) LOYO SR (drop each year, recompute 2008+ SR):')
for y in sorted(yr.index):
    sub=netv08[netv08.index.year!=y]
    print(f'   -{y}: SR {sub.mean()/sub.std()*np.sqrt(252):.3f}', end='')
    if (y-2008)%4==3: print()
print()
print('9) scrub10 (drop 10 worst days):')
worst=netv08.nsmallest(10).index
s9=netv08.drop(worst)
print(f'   SR {s9.mean()/s9.std()*np.sqrt(252):.3f}')
