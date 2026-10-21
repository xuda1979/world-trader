"""FINAL reality check on OVNCAP before honest verdict: instrument-level audit of what would
have to be true for the paper PnL to be real. Show: (1) a sample name-day: what position stream
w*on - w*ic implies (sell at open, short same name same day); (2) short-open-position borrow+
HTB reality; (3) correlation of w*on-w*ic with vix regime; (4) verdict inputs."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=H.xs_ls(sig,k=k)
p=pos.shift(1).fillna(0.0)

# (1) sample name-day mechanics
t=pd.Timestamp('2015-06-01')
row=p.loc[t]
name=row.abs().idxmax()
print(f'sample day {t.date()}: name {name}, w={row[name]:+.3f}, on={on.loc[t,name]:+.4f} ({on.loc[t,name]*1e4:.1f}bp), ic={ic.loc[t,name]:+.4f}')
print(f'  paper PnL contribution: {row[name]*(on.loc[t,name]-ic.loc[t,name])*1e4:.1f}bp')
print(f'  to earn +w*on_t: held from prior close to open_t then SOLD at open_t;')
print(f'  to ALSO earn -w*ic_t: must SHORT {name} from open_t to close_t. Two executions.')

# (3) regime: vix
import pandas as pd
vix=pd.read_csv('/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix_daily.csv',index_col=0,parse_dates=True)['vix']
vix=vix[~vix.index.duplicated(keep='last')].sort_index()
r1=on.fillna(0.0); r2=ic.fillna(0.0)
turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
net=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor).dropna()
rv=net.expanding(60).std()*np.sqrt(252); sc=(0.10/rv).clip(upper=3.0).shift(1).fillna(1.0)
netv=(net*sc).dropna(); n08=netv[netv.index>='2008-01-01']
v=vix.reindex(n08.index).ffill()
vz=(v-v.rolling(252).mean())/v.rolling(252).std()
hi=vz>0; lo=vz<=0
print(f'VIX-high days: SR {n08[hi].mean()/n08[hi].std()*np.sqrt(252):.2f} (n={hi.sum()}) | VIX-low: SR {n08[lo].mean()/n08[lo].std()*np.sqrt(252):.2f} (n={lo.sum()})')
# (4) borrow on the short-at-open structure: shorts ~ gross 1.0 => 0.5%/yr charged; HTB hard-to-borrow
# small caps in top-momentum decile could be 5-20%/yr — sensitivity:
for extra_bps in [0,50,200,500]:
    b2=(0.005+extra_bps/1e4)/252
    bor2=p.clip(upper=0).abs().sum(axis=1)*b2
    n3=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor2).dropna()
    s3=n3[n3.index>='2008-01-01']
    print(f'borrow {0.5+extra_bps}/yr (gross paper): SR {s3.mean()/s3.std()*np.sqrt(252):.3f}')
