#!/usr/bin/env python3
"""G1: Parkinson range-vol HARVEST (variance risk premium proxy) on 8 FX pairs.
Daily: per-pair Parkinson vol (lags<=t) vs trailing close-close vol; position LONG a pair's
range when Parkinson>>cc-vol (range rich -> sell realized? NO tradable vol in spot).
HONEST translation: the only spot-executable harvest of a RANGE premium is a mean-reversion
conditioned on range richness. We test: next-day reversion (fade open<-prev close divergence)
gated by Parkinson percentile. 2x2x2 sweep: gate {on/off} x reversion lookback {1,3} x L/S.
Weekly decision variant too. All T+1, 6bps, daily PnL, gates per charter."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FXMICRO/scripts')
from fxmicro_lib import *
from campaign.agents.B2_highfreq.gates import run_gates
import campaign.results  # noqa
ROOTx=ROOT

px=load_px()
CL=pd.DataFrame({p:px[p]['close'] for p in PAIRS}).sort_index()
OP=pd.DataFrame({p:px[p]['open'] for p in PAIRS}).sort_index()
HI=pd.DataFrame({p:px[p]['high'] for p in PAIRS}).sort_index()
LO=pd.DataFrame({p:px[p]['low'] for p in PAIRS}).sort_index()
CL=CL.dropna(how='all'); common=CL.dropna().index
for D in (CL,OP,HI,LO): 
    pass
# restrict to common tradable window (all 8 alive)
start=common.min()
CL=CL[CL.index>=start]; OP=OP[OP.index>=start]; HI=HI[HI.index>=start]; LO=LO[LO.index>=start]

RET=CL.pct_change()
def parkinson(HI,LO,lb):
    lf=np.log(HI/LO.replace(0,np.nan))
    pk=(lf**2/(4*np.log(2))).rolling(lb,min_periods=lb//2).mean()
    return np.sqrt(pk*252)
def ccvol(RET,lb):
    return RET.rolling(lb,min_periods=lb//2).std()*np.sqrt(252)

def run(gate_on, lb, lookback, decision):
    sig=pd.DataFrame(0.0,index=CL.index,columns=PAIRS)
    oc=(CL-OP)/OP                      # today's O->C move (known at close t)
    prevgap=(OP-CL.shift(1))/CL.shift(1)
    drv=-np.sign(prevgap)*np.abs(prevgap)  # fade the overnight gap (prev close -> today open)
    pk=parkinson(HI,LO,lb); cv=ccvol(RET,lb)
    rich=(pk>cv) if gate_on else pd.DataFrame(True,index=CL.index,columns=PAIRS)
    if lookback==1:
        base=-np.sign(RET)
    else:
        base=-np.sign(RET.rolling(lookback).sum())
    sig=base.where(rich)*0.125*np.ones((1,8))
    sig=sig.shift(0)   # info at t: uses RET up to t, PK up to t
    net,turn=bt_longshort(sig.fillna(0),CL,decision=decision)
    net=net[net.index>pd.Timestamp(start)+pd.Timedelta(days=120)]
    return net

if __name__=='__main__':
    blend=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv',
                      index_col=0,parse_dates=True).iloc[:,0]
    rows=[]
    for gate_on in [True,False]:
        for lb in [21,63]:
            for lbk in [1,3,5]:
                for dec in ['daily','weekly']:
                    net=run(gate_on,lb,lbk,dec)
                    if len(net)<400: continue
                    s=full_stats(net); h1,h2=halves_sr(net)
                    fg=flatten_gate(net,'g1')
                    j=pd.concat([net,blend],axis=1).dropna()
                    corr=float(np.corrcoef(j.iloc[:,0],j.iloc[:,1])[0,1]) if len(j)>250 else np.nan
                    pv,real=scramble_pval(net,n=200,seed=0)
                    rows.append(dict(gate=gate_on,pklb=lb,revlb=lbk,dec=dec,sr=round(s['sr'],2),
                        ann=round(s['ann'],1),mdd=round(s['mdd'],1),H1=round(h1,2),H2=round(h2,2),
                        negy=s['negy'],worst=round(s['worst'],1),scrp=round(pv,3),corr=round(corr,3),
                        ac1=fg['ac1'],uq=fg['uniq_ratio']))
    df=pd.DataFrame(rows).sort_values('sr',ascending=False)
    pd.set_option('display.width',250)
    print(df.to_string(index=False))
    df.to_csv(f'{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/g1_grid.csv',index=False)
