"""Repro: campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv
Brent-WTI log-spread mean-reversion stat-arb. T+1, 6bps, trailing 10% vol-target.
""" 
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target

def run(lookback=15, buy_z=1.5, cost=6, min_start='2008-01-01'):
    BR=fred('brent').dropna(); WT=fred('wti').dropna()
    sp=(np.log(BR)-np.log(WT)).dropna()
    sp=sp[sp.index>=min_start]
    z=(sp-sp.rolling(lookback,min_periods=lookback).mean())/sp.rolling(lookback,min_periods=lookback).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index); pos[z < -buy_z]=1.0; pos[z>buy_z]=-1.0
    ret=sp.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=gr-tup*cost/1e4
    return net.dropna()

def main():
    net=run(lookback=15,buy_z=1.5,cost=6)
    scaled,_=vol_target(net)
    out=pd.DataFrame({'ret':scaled.values},index=scaled.index); out.index.name='date'
    out.to_csv('campaign/agents/B2_highfreq/sleeves/brwt_spread_rev15.csv')
    print('wrote', len(out))

if __name__=='__main__': main()
