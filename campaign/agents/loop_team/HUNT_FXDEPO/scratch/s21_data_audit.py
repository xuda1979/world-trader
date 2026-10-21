"""DATA AUDIT for the record: DEX H.10 series vintage — these are NOON BUYING RATES
(4pm Toronto cross rates before 1999), not executable spot. Document stale-print and
publication-lag facts; test robustness of FXD1 to +1 execution day (T+2) and to
zero-return-day filtering (drop days where either leg didn't print)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXDEPO/scratch')
from lib import *

px=pd.DataFrame({n:dex(n) for n in ['DEXKOUS','DEXSDUS','DEXSFUS','DEXNOUS']})
lp=np.log(px); rets=px.pct_change()
books=[('DEXKOUS','DEXSDUS'),('DEXKOUS','DEXSFUS'),('DEXKOUS','DEXNOUS')]

def build(lbs=(21,63), extra_lag=0, drop_zero=False):
    rs=[]
    for a,b in books:
        sp=lp[a]-lp[b]
        pos=sum(zpos(sp,lb,2.0) for lb in lbs)/2
        if drop_zero:
            m=(rets[a].shift(1)!=0)&(rets[b].shift(1)!=0)
            pos=pos.where(m,0.0)
        P=pd.DataFrame({a:pos,b:-pos})
        R=pd.DataFrame({a:rets[a],b:rets[b]})
        net=net_of_book(P,R)
        if extra_lag:
            # re-derive with signal shifted one extra day: pos.shift(extra_lag)
            ps=P.shift(1+extra_lag).fillna(0)
            gross=(ps*R.reindex(ps.index).fillna(0)).sum(axis=1)
            turn=(ps.diff().abs()/2.0).fillna(0).sum(axis=1)
            bor=BORROW*ps.clip(upper=0).abs().sum(axis=1)
            net=(gross-turn*COST-bor)
        rs.append(net.fillna(0))
    return pd.concat(rs,axis=1).sum(axis=1)/3

r=build(); r8=r[r.index>='2008-01-01']
print('as-built: SR %.3f'%full_stats(r8)['sr'])
r2=build(extra_lag=1); r28=r2[r2.index>='2008-01-01']
print('T+2 (extra lag): SR %.3f'%full_stats(r28)['sr'])
rz=build(drop_zero=True); rz8=rz[rz.index>='2008-01-01']
print('zero-print days filtered: SR %.3f (n=%d)'%(full_stats(rz8)['sr'],full_stats(rz8)['n']))
# H.10 missing-day structure: how many days does KO/SD print on Fed holiday rows?
print('\nSat/Sun rows in DEX panel?', int((px.index.dayofweek>=5).sum()))
