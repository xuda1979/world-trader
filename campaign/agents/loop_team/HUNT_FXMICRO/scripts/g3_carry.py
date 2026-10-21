#!/usr/bin/env python3
"""G3: carry via rate DIFFS on the 8 tradable pairs (charter idea 3), with ACCRUAL.
Sign convention: series pct_change = return of holding 1 unit of FIRST ccy (in 2nd ccy).
Long FIRST ccy accrues (10y_BASE - 10y_QUOTE)/252 per day; position -1 flips sign.
Books:
  C1 always-on rate-diff carry (all 8 pairs, pos sign = sign of base-minus-quote diff)
  C2 same, top-3/bottom-3 by diff only (extremes)
  C3 always-on but vol-inverse weighted, weekly decision
  C4 carry gate: hold carry sign only when |diff| in middle of its own trailing 12m range... (disclosed)
All PIT (monthly yields, value m usable m+1), T+1, 6bps, vt gates, flatten gate, corr to blend."""
import sys, numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
sys.path.insert(0,ROOT); sys.path.insert(0,ROOT+'/campaign/agents/loop_team/HUNT_FXMICRO/scripts')
from fxmicro_lib import *
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr, scramble_pval

px=load_px()
CL=pd.DataFrame({p:px[p]['close'] for p in PAIRS}).sort_index()
CL=CL.dropna(how='all'); start=CL.dropna().index.min(); CL=CL[CL.index>=start]
RET=CL.pct_change()
V=RET.rolling(63,min_periods=40).std()
W=(1.0/V); W=W.div(W.mean(axis=1),axis=0)*0.125
ACC=pd.DataFrame({p:accrual_series(p,CL.index) for p in PAIRS})   # per-day accrual for +1 unit

def run(mode, dec):
    if mode=='C1': sig=np.sign(ACC)*W
    elif mode=='C2':
        r=ACC.rank(axis=1)-4.5
        sig=np.sign(r)*W
    elif mode=='C3': sig=np.sign(ACC)*W
    elif mode=='C4':
        roll_hi=ACC.rolling(252,min_periods=126).max(); roll_lo=ACC.rolling(252,min_periods=126).min()
        mid=(roll_hi+roll_lo)/2; w=(ACC-mid).abs()/(roll_hi-roll_lo).replace(0,np.nan)
        sig=np.sign(ACC)*(w>0.5)*W     # only when diff far from its 12m mid
    net,_=bt_longshort(sig.fillna(0),CL,decision=dec)
    return net[net.index>pd.Timestamp(start)+pd.Timedelta(days=180)], sig

if __name__=='__main__':
    blend=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv',
                      index_col=0,parse_dates=True).iloc[:,0]
    rows=[]
    for mode in ['C1','C2','C3','C4']:
        for dec in ['daily','weekly']:
            net,sig=run(mode,dec)
            if len(net)<400: continue
            s=full_stats(net); h1,h2=halves_sr(net); fg=flatten_gate(net)
            j=pd.concat([net,blend],axis=1).dropna()
            corr=float(np.corrcoef(j.iloc[:,0],j.iloc[:,1])[0,1])
            pv,_=scramble_pval(net,n=200,seed=0)
            rows.append(dict(mode=mode,dec=dec,sr=round(s['sr'],2),ann=round(s['ann'],1),
                mdd=round(s['mdd'],1),H1=round(h1,2),H2=round(h2,2),negy=s['negy'],
                worst=round(s['worst'],1),scrp=round(pv,3),corr=round(corr,3),
                ac1=fg['ac1'],uq=fg['uniq_ratio']))
    df=pd.DataFrame(rows).sort_values('sr',ascending=False)
    pd.set_option('display.width',250)
    print(df.to_string(index=False))
    df.to_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/g3_grid.csv',index=False)
