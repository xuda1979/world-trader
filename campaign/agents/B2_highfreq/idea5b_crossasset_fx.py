"""Cross-asset reversal incl FX. T+1, 6bps, vol-targeted."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr, scramble_pval

FX = {'EUR_USD':'EUR_USD','GBP_USD':'GBP_USD','USD_JPY':'USD_JPY','USD_CHF':'USD_CHF','USD_CAD':'USD_CAD','AUD_USD':'AUD_USD'}
def build_all(min_start='2008-01-01'):
    P={}
    for a in ['us10y','us2y','dxy','xau','wti','brent','vix']:
        s=fred(a).dropna(); P[a]=s
    import glob,os
    for pair,n in FX.items():
        f=f"/Users/daxu/software/world-trader/tools/quant/data/fx/{pair}.csv"
        df=pd.read_csv(f,index_col=0,parse_dates=True)
        col='close' if 'close' in df.columns else df.columns[0]
        P[pair]=df[col].dropna()
    px=pd.DataFrame(P).sort_index()
    px=px[px.index>=min_start]
    return px

def run(L,dirn='rev',n_low=2,n_high=2,min_start='2008-01-01',clip=0.5):
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

def position_shuffle_test(pos, fwd, n=200, seed=0):
    """Proper signal-scramble: keep returns in time order, shuffle positions across time.
    real SR vs distribution of shuffled SRs."""
    rng=np.random.default_rng(seed)
    gr=(pos*fwd).sum(axis=1).values
    tup=pos.diff().abs().sum(axis=1)/2.0
    net=gr-tup*6/1e4
    scaled,sc=vol_target(pd.Series(net,index=pos.index))
    real=full_stats(scaled)['sr']
    cnt=0
    idx=pos.index.values
    for _ in range(n):
        perm=rng.permutation(len(pos))
        pos_s=pos.values[perm]
        pos_sh=pd.DataFrame(pos_s,index=pos.index,columns=pos.columns)
        gr_s=(pos_sh*fwd).sum(axis=1)
        tup_s=pos_sh.diff().abs().sum(axis=1)/2.0
        net_s=gr_s-tup_s*6/1e4
        sc_s,_=vol_target(pd.Series(net_s,index=pos.index))
        s_s=full_stats(sc_s)['sr']
        if s_s>=real: cnt+=1
    return cnt/n, real

if __name__=='__main__':
    px=build_all()
    print("universe n =",px.shape[1],"rows",px.shape[0])
    for dirn in ['rev','mom']:
        for L in [2,3,5,8]:
            net,gr,tup,px=run(L,dirn,2,2)
            if len(net)<300: continue
            scaled,_=vol_target(net)
            s=full_stats(scaled); h1,h2=halves_sr(scaled)
            print(f"{dirn} L={L}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% H1={h1:.2f} H2={h2:.2f} negY={s['negy']} worst={s['worst']:.1f}%")
