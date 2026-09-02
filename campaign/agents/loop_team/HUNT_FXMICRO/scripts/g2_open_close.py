#!/usr/bin/env python3
"""G2: open-close REVERSAL engines on 8 FX pairs (charter idea 2).
Family A: fade the previous day's O->C move (classic daily FX reversal).
Family B: fade the gap (prev close -> today open) — separate tradeable leg.
Family C: A+B combined with vol scaling and |move| z-gating (only fade EXTREME moves).
Sweeps: lookback {1,2,3}, z-threshold {0,0.5,1.0}, weighting {eqw, vol-inv}, {daily,weekly}.
T+1, 6bps/side, flatten gate + full gates + corr to HONEST11-L16 blend."""
import sys, numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
sys.path.insert(0,ROOT); sys.path.insert(0,ROOT+'/campaign/agents/loop_team/HUNT_FXMICRO/scripts')
from fxmicro_lib import *
from campaign.agents.B2_highfreq.gates import full_stats, halves_sr, scramble_pval

px=load_px()
CL=pd.DataFrame({p:px[p]['close'] for p in PAIRS}).sort_index()
OP=pd.DataFrame({p:px[p]['open'] for p in PAIRS}).sort_index()
CL=CL.dropna(how='all'); start=CL.dropna().index.min()
CL=CL[CL.index>=start]; OP=OP.reindex(CL.index)
RET=CL.pct_change()
OC=(CL-OP)/OP                      # intraday O->C (known at t close)
GAP=(OP-CL.shift(1))/CL.shift(1)   # overnight gap (known at t open)

def zsc(df, lb=63):
    m=df.rolling(lb,min_periods=lb//2).mean(); s=df.rolling(lb,min_periods=lb//2).std()
    return (df-m)/s.replace(0,np.nan)

def run(family, lbk, zth, dec, volw=True):
    if family=='oc': move=OC; sig=-np.sign(move.rolling(lbk).sum())
    elif family=='gap': move=GAP; sig=-np.sign(move.rolling(lbk).sum())
    elif family=='zoc': move=OC; z=zsc(OC,63); sig=-np.sign(z.where(z.abs()>zth, 0.0))
    elif family=='contoc': move=OC; sig=np.sign(move.rolling(lbk).sum())   # continuation control
    elif family=='contgap': move=GAP; sig=np.sign(move.rolling(lbk).sum())
    else: raise ValueError(family)
    if volw:
        v=RET.rolling(63,min_periods=40).std()
        w=(1.0/v)
        w=w.div(w.mean(axis=1),axis=0)*0.125
        sig=sig*w
    else:
        sig=sig*0.125
    net,turn=bt_longshort(sig.fillna(0.0),CL,decision=dec)
    return net[net.index>pd.Timestamp(start)+pd.Timedelta(days=90)]

if __name__=='__main__':
    blend=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv',
                      index_col=0,parse_dates=True).iloc[:,0]
    rows=[]
    for fam in ['oc','gap','zoc','contoc','contgap']:
        for lbk in [1,2,3]:
            for zth in ([0,0.5,1.0] if fam=='zoc' else [0]):
                for dec in ['daily','weekly']:
                    net=run(fam,lbk,zth,dec)
                    if len(net)<400: continue
                    s=full_stats(net); h1,h2=halves_sr(net)
                    fg=flatten_gate(net)
                    j=pd.concat([net,blend],axis=1).dropna()
                    corr=float(np.corrcoef(j.iloc[:,0],j.iloc[:,1])[0,1])
                    pv,_=scramble_pval(net,n=200,seed=0)
                    rows.append(dict(fam=fam,lbk=lbk,zth=zth,dec=dec,sr=round(s['sr'],2),
                        ann=round(s['ann'],1),mdd=round(s['mdd'],1),H1=round(h1,2),H2=round(h2,2),
                        negy=s['negy'],worst=round(s['worst'],1),scrp=round(pv,3),corr=round(corr,3)))
    df=pd.DataFrame(rows).sort_values('sr',ascending=False)
    pd.set_option('display.width',250)
    print(df.to_string(index=False))
    df.to_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/g2_grid.csv',index=False)
