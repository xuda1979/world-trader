"""Cross-asset reversal WITHOUT vix (vix extreme jumps dominate). T+1 6bps vol-target."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr

def build_all(min_start='2008-01-01'):
    P={}
    for a in ['us10y','us2y','dxy','xau','wti','brent']:
        s=fred(a).dropna(); P[a]=s
    pairs=['EUR_USD','GBP_USD','USD_JPY','USD_CHF','USD_CAD','AUD_USD','NZD_USD']
    for pair in pairs:
        f=f"/Users/daxu/software/world-trader/tools/quant/data/fx/{pair}.csv"
        df=pd.read_csv(f,index_col=0,parse_dates=True)
        col='close' if 'close' in df.columns else df.columns[0]
        P[pair]=df[col].dropna()
    px=pd.DataFrame(P).sort_index()
    return px[px.index>=min_start]

def run(L,dirn='rev',n_low=2,n_high=2,min_start='2008-01-01',clip=0.3):
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
    return net.dropna(),gr.dropna(),tup.dropna(),px

if __name__=='__main__':
    px=build_all(); print("n assets",px.shape[1])
    for L in [5,8,10,15]:
        net,gr,tup,_=run(L,'rev',2,2)
        scaled,_=vol_target(net)
        s=full_stats(scaled); h1,h2=halves_sr(scaled)
        print(f"rev L={L}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% H1={h1:.2f} H2={h2:.2f} negY={s['negy']} worst={s['worst']:.2f}% turn={tup.mean():.2f}")
