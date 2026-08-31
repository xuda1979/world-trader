"""Idea 5: cross-asset short momentum/reversal on FRED assets. T+1, 6bps/side, vol-targeted."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats

ASSETS = ['us10y','us2y','dxy','xau','wti','brent']

def build_panel(min_start='2008-01-01'):
    P={}
    for a in ASSETS:
        s=fred(a).dropna()
        if len(s)>0: P[a]=s
    df=pd.DataFrame(P).sort_index()
    df=df[df.index>=min_start]
    return df

def run(L, dirn='rev', n_low=2, n_high=2, min_start='2008-01-01', clip=0.5):
    px=build_panel(min_start)
    past=px.pct_change(L).clip(-clip,clip)
    fwd=px.pct_change(1).shift(-1).clip(-clip,clip)
    n=px.shape[1]
    rank=past.rank(axis=1,na_option='keep')
    if dirn=='rev':
        long_mask=(rank<=n_low); short_mask=(rank>(n-n_high))
    else:
        long_mask=(rank>(n-n_low)); short_mask=(rank<=n_high)
    pos=pd.DataFrame(0.0,index=px.index,columns=px.columns)
    pos[long_mask]=1.0/n_low; pos[short_mask]=-1.0/n_high
    valid=past.notna()&fwd.notna()&px.notna()
    pos=pos.where(valid,0.0)
    gr=(pos*fwd).sum(axis=1)
    tup=pos.diff().abs().sum(axis=1)/2.0
    net=gr-tup*6.0/1e4
    return net.dropna(),gr.dropna(),tup.dropna()

if __name__=='__main__':
    for dirn in ['rev','mom']:
        for L in [3,5,10,20]:
            for nl,nh in [(2,2),(3,3)]:
                net,gr,tup=run(L,dirn,nl,nh)
                if len(net)<300: continue
                scaled,sc=vol_target(net)
                if scaled.notna().sum()<300: continue
                s=full_stats(scaled)
                print(f"{dirn} L={L} nl={nl} nh={nh}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% turn={tup.mean():.2f}")
