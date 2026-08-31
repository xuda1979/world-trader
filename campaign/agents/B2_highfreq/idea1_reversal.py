"""Idea 1: short-horizon cross-sectional reversal. Full pipeline with vol target + gates."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.bt import load_px, backtest
from campaign.agents.B2_highfreq.gates import vol_target, run_gates, full_stats, halves_sr, scramble_pval

def build(L,k):
    px=load_px()
    past=px.pct_change(L)
    rank=past.rank(axis=1,na_option='keep')
    n=px.shape[1]
    long_mask=(rank<=k); short_mask=(rank>(n-k))
    pos=pd.DataFrame(0.0,index=px.index,columns=px.columns)
    pos[long_mask]=1.0/k; pos[short_mask]=-1.0/k
    net,gr,tup=backtest(px,pos)
    return net,gr,tup

if __name__=='__main__':
    # sweep
    best=None
    for L in [3,5,7,10]:
        for k in [15,20,30,40]:
            net,gr,tup=build(L,k)
            scaled,scale=vol_target(net)
            s=full_stats(scaled)
            print(f"L={L} k={k}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% turn={tup.mean():.2f}")
            if best is None or s['sr']>best[0]: best=(s['sr'],L,k)
    print("BEST:",best)
