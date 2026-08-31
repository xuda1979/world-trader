"""Final candidate: cross-asset reversal, vix included, clip=0.18, L=8, 2/2. Full gates."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

FINAL = dict(L=8, dirn='rev', n_low=2, n_high=2, clip=0.18)

def build_all(min_start='2008-01-01'):
    P={}
    for a in ['us10y','us2y','dxy','xau','wti','brent','vix']:
        P[a]=fred(a).dropna()
    for pair in ['EUR_USD','GBP_USD','USD_JPY','USD_CHF','USD_CAD','AUD_USD']:
        df=pd.read_csv(f"/Users/daxu/software/world-trader/tools/quant/data/fx/{pair}.csv",index_col=0,parse_dates=True)
        col='close' if 'close' in df.columns else df.columns[0]
        P[pair]=df[col].dropna()
    px=pd.DataFrame(P).sort_index()
    return px[px.index>=min_start]

def run(L=8,dirn='rev',n_low=2,n_high=2,clip=0.18,min_start='2008-01-01'):
    px=build_all(min_start)
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

def main():
    # reproduces sleeve shot: crossasset_rev_L8 (vol-targeted daily returns)
    from campaign.agents.B2_highfreq.gates import vol_target
    import pandas as pd
    net,gr,tup = run(L=8,dirn='rev',n_low=2,n_high=2,clip=0.18)
    scaled,_ = vol_target(net)
    out = pd.DataFrame({'ret':scaled.values}, index=scaled.index); out.index.name='date'
    out.to_csv('campaign/agents/B2_highfreq/sleeves/crossasset_rev_L8.csv')
    print('wrote sleeve', len(out), 'rows')

if __name__=='__main__':
    main()
