#!/usr/bin/env python3
"""G4: execution-edge microstructure (charter idea 1 residual): does TRADING AT A BETTER
PRICE within the documented day remove the 6bps drag enough to flip any engine positive?
Honest model: our data has only daily OHLC. Limit fills are NOT observable, so we can only
bound: assume deterministic fill at open + k*(high-low) in the favorable direction whenever
the day's range crosses the level. This is an OPTIMISTIC bound (limit-fill models are known
to embed lookahead: you fill only when it helps you => adverse selection ignored).
We quantify the bound for the best G-family (CPWR fade hold2): trade at open instead of close.
Also: mid-quote entry (open+close)/2 bound. All documented as bounds, NOT sleeves."""
import sys, numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
sys.path.insert(0,ROOT); sys.path.insert(0,ROOT+'/campaign/agents/loop_team/HUNT_FXMICRO/scripts')
from fxmicro_lib import *

px=load_px()
CL=pd.DataFrame({p:px[p]['close'] for p in PAIRS}).sort_index()
CL=CL.dropna(how='all'); start=CL.dropna().index.min(); CL=CL[CL.index>=start]
RET=CL.pct_change()
OP=pd.DataFrame({p:px[p]['open'] for p in PAIRS}).reindex(CL.index)
HI=pd.DataFrame({p:px[p]['high'] for p in PAIRS}).reindex(CL.index)
LO=pd.DataFrame({p:px[p]['low'] for p in PAIRS}).reindex(CL.index)
cpwr=((CL-LO)/(HI-LO).replace(0,np.nan))
sig0=(-np.sign(cpwr-0.5))
kr=np.arange(len(sig0))%2==0
sig=sig0.where(pd.Series(kr,index=sig0.index)).ffill()
sigT=sig.shift(1)
V=RET.rolling(63,min_periods=40).std()
W=(1.0/V); W=W.div(W.mean(axis=1),axis=0)*0.125
sigW=sigT*W

# close-to-close base (what we had):
base=(sigW*RET).sum(axis=1)
turn=sigW.diff().abs().sum(axis=1).fillna(0)
print('close-to-close: gross bps/d %.3f cost bps/d %.3f'%(base.mean()*1e4, (turn*6e-4).mean()*1e4))

# open-entry bound: position decided at close t-1, entered at open t, exited at open t+1.
# PnL_leg = w * (Open_{t+1}/Open_t - 1)  (the strategy holds t open -> t+1 open)
ret_open=OP.pct_change()
base_open=(sigW*ret_open).sum(axis=1)
# turnover cost stays 6bps but fill at open has ~0 spread difference in this model; also
# the official-recipe cost is unchanged. Costs are on the same |dsig|.
print('open-to-open  : gross bps/d %.3f cost bps/d %.3f'%(base_open.mean()*1e4,(turn*6e-4).mean()*1e4))

# mid-entry bound
MID=(OP+CL)/2
ret_mid=MID.pct_change()
base_mid=(sigW*ret_mid).sum(axis=1)
print('mid-to-mid    : gross bps/d %.3f cost bps/d %.3f'%(base_mid.mean()*1e4,(turn*6e-4).mean()*1e4))

# breakeven cost per side for close-to-close variant:
be=base.mean()/turn.mean()*1e4
print('breakeven cost = %.2f bps/side (mandated 6)'%be)
