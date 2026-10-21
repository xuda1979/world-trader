"""Coordinator KF industry momentum v2 — clean implementation.
Book: rank industries by trailing sum of returns; long top-ntop EW, short bottom-ntop EW.
Rebalance every `rebal` days (hold in between). mode: mom (winners-long) / rev (losers-long).
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats
from coord_kf_indmom import load_kf

def ind_book(ret, lookback=63, ntop=3, rebal=5, mode='mom'):
    dates=ret.index[::rebal]
    pos=pd.DataFrame(0.0,index=ret.index,columns=ret.columns)
    mom=ret.rolling(lookback).sum()
    sign = 1.0 if mode=='mom' else -1.0
    for d in dates:
        m=mom.loc[:d].iloc[-1].dropna()
        if len(m)<20: continue
        s=m.sort_values()
        pos.loc[d, s.index[:ntop]] = -sign/ntop
        pos.loc[d, s.index[-ntop:]] = sign/ntop
    nz=pos.loc[[d for d in dates if d in pos.index]]
    pos_h=nz.reindex(ret.index).ffill().fillna(0)
    gross=(pos_h.shift(1)*ret.fillna(0)).sum(axis=1)
    to=pos_h.diff().abs().sum(axis=1)/2
    net=gross-to*6e-4
    return net.dropna()

if __name__=='__main__':
    vw=load_kf('48_Industry_Portfolios_Daily.csv')
    vw=vw[vw.index>='1990-01-01']
    print("48ind VW", vw.shape)
    results={}
    for lb in [21,63,126,252]:
        for mode in ['mom','rev']:
            for rebal in [1,5,21]:
                r=ind_book(vw,lookback=lb,ntop=3,rebal=rebal,mode=mode)
                sc,_=vol_target(r)
                r08=sc[sc.index>='2008-01-01']
                st=full_stats(r08)
                h=len(r08)//2; h1=full_stats(r08.iloc[:h]); h2=full_stats(r08.iloc[h:])
                key=f"{mode} lb{lb} rb{rebal}"
                results[key]=(st,h1,h2,r08)
                print(f"{key:20s} SR={st['sr']:5.2f} ann={st['ann']:6.1f}% mdd={st['mdd']:6.1f}% H1={h1['sr']:5.2f} H2={h2['sr']:5.2f} negy={st['negy']}")
