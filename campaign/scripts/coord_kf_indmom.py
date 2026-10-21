"""Coordinator: KF 48-industry daily — industry momentum + reversal, exact harness gates.
T+1, 6bps on book turnover, trailing vol-target 10%. Honest: halves, yearly, scramble.
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

KF='/Users/daxu/software/world-trader/tools/quant/data/kenfrench'
def load_kf(fn, section="Average Value Weighted Returns -- Daily"):
    lines=open(f'{KF}/{fn}').read().split('\n')
    si=[i for i,l in enumerate(lines) if section in l][0]
    hdr=[h.strip().strip(',') for h in lines[si+1].split(',')]
    rows=[]
    for l in lines[si+2:]:
        parts=[p.strip() for p in l.split(',')]
        if len(parts)!=len(hdr) or not parts[0].isdigit(): break
        rows.append(parts)
    df=pd.DataFrame(rows).astype(float)
    df.index=pd.to_datetime(df.iloc[:,0],format='%Y%m%d')
    df=df.iloc[:,1:]
    df.columns=hdr[1:]
    return df/100.0

def ind_book(ret48, lookback=63, ntop=3, mode='mom', rebal=5):
    """Top-N minus bottom-N industry book, rebalanced every `rebal` days."""
    mom=ret48.rolling(lookback).sum()
    dates=ret48.index[::rebal]
    pos=pd.DataFrame(0.0,index=ret48.index,columns=ret48.columns)
    for d in dates:
        m=mom.loc[:d].iloc[-1].dropna()
        if len(m)<20: continue
        s=m.sort_values()
        pos.loc[d,s.index[:ntop]]=-1.0/ntop
        pos.loc[d,s.index[-ntop:]]=1.0/ntop
    pos=pos.replace(0,np.nan).ffill(limit=rebal-1).fillna(0) if False else pos
    # hold positions until next rebal: reindex pos to all days via ffill on non-zero rows
    nz=pos.loc[dates]
    pos_h=nz.reindex(ret48.index).ffill().fillna(0)
    gross=(pos_h.shift(1)*ret48).sum(axis=1)
    to=pos_h.diff().abs().sum(axis=1)/2
    net=gross-to*6e-4
    return net.dropna()

if __name__=='__main__':
    vw=load_kf('48_Industry_Portfolios_Daily.csv')
    print("48ind VW", vw.shape, vw.index[0].date(), vw.index[-1].date())
    for lb in [21,63,126]:
        for mode in ['mom','rev']:
            r=ind_book(vw,lookback=lb,mode=mode)
            sc,_=vol_target(r)
            r08=sc[sc.index>='2008-01-01']
            st=full_stats(r08)
            h=len(r08)//2; h1=full_stats(r08.iloc[:h]); h2=full_stats(r08.iloc[h:])
            print(f"48ind {mode} lb{lb:3d}: SR={st['sr']:5.2f} ann={st['ann']:6.1f}% mdd={st['mdd']:6.1f}% H1={h1['sr']:5.2f} H2={h2['sr']:5.2f} negy={st['negy']}")
