"""P6c: champion dependence diagnostic — rebuild HONEST14V3 without QAxasts contribution.
Read pool sleeves, compute the champion minus QAxasts-sleeve contribution (leave-one-out
at the RETURN level, honest label: DIAGNOSTIC, not a deliverable)."""
import sys; sys.path.insert(0,'.')
from libb import *
import pandas as pd, numpy as np
ROOT='/Users/daxu/software/world-trader'
sys.path.insert(0,f'{ROOT}/campaign/scripts')
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True).iloc[:,0]
# load all 14 pool sleeves (11 + diescrack + CFX4 + FF2)
import honest11_build as HB
sleeves={}
for n,p in HB.POOL.items():
    sleeves[n]=HB.sn(p)
import glob, os
def sn_abs(path):
    r=pd.read_csv(path,index_col=0,parse_dates=True).iloc[:,0].dropna()
    keep=np.array([(d.dayofweek<5 and d.date() not in HB.hol) for d in r.index])
    out=pd.Series(0.0,index=r.index[keep]); cu=0.0; ki=0; v=r.values
    for i in range(len(r)):
        cu+=v[i]
        if keep[i]: out.iloc[ki]=cu; cu=0.0; ki+=1
    return out.iloc[:ki]
for n,path in {'diescrack_L40Z20':f'{ROOT}/campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv'}.items():
    sleeves[n]=sn_abs(path)
sleeves['CFX4']=sn_abs(f'{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_carry_raw_daily.csv')
sleeves['FF2']=sn_abs(f'{ROOT}/campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_raw_daily.csv')
names=list(sleeves)
print('pool:',names)
# each sleeve already vt10-ish via sn+pool construction; champion uses per-sleeve vt at 0.08/0.10
# LOO at equal-vt mean level (diagnostic): compute vt'ed returns per pool weight
V={}
for n in names:
    r=sleeves[n]
    v,s=HB.vt(r,0.10)
    V[n]=v
V=pd.DataFrame(V)
pool=V.dropna(how='all')
base=pool.mean(axis=1).dropna()
import lib as F
s0=F.full_stats(base.dropna())
print(f"equal-wt vt10 14-pool: SR {s0['sr']:.3f} ann_geo {s0['ann_geo']*100:.1f}% MDD {s0['mdd']*100:.1f}%")
# LOO drop QAxasts
b2=pool.drop(columns=['QAxasts']).mean(axis=1).dropna()
s2=F.full_stats(b2)
print(f"drop-QAxasts      : SR {s2['sr']:.3f} ann_geo {s2['ann_geo']*100:.1f}% MDD {s2['mdd']*100:.1f}%")
# LOO drop each: table
for n in names:
    b=pool.drop(columns=[n]).mean(axis=1).dropna()
    sb=F.full_stats(b)
    print(f"  drop {n:16s}: SR {sb['sr']:.3f} ann {sb['ann_geo']*100:+.1f}%")
