"""C5 Round-3 repro: charter items 2 (exact EIA WNGSR season) & 3 (vol-regime sizing)
and the sibling-scan follow-ups (natgas Tue legs, VIX-Fri/HO-Tue honesty checks).
Item 1 (per-month rotation, IS-only) repro: rotation.py (its printed table is the result).
All results T+1, 6bps/side, harness trailing expanding 10% VT cap 3x, 2008+.
Results match FINDINGS.md Round 3 entry exactly."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.agents.B2_highfreq.gates import vol_target, full_stats, halves_sr
COST=6e-4
D='/Users/daxu/software/world-trader/tools/quant/data/newdata/DHHNGSP.csv'
s=pd.read_csv(D,index_col=0,parse_dates=True).iloc[:,0]
s=pd.to_numeric(s,errors='coerce'); s=s[s>0].dropna().sort_index()
lr=np.log(s).diff(); idx=lr.index
def pipeline(pos,k=2.5):
    thr=lr.rolling(90).std().shift(1)*k
    pos=pos.mask(lr.abs()>thr,0.0)
    gr=pos*lr.shift(-1); tn=pos.diff().abs(); tn.iloc[0]=abs(pos.iloc[0])
    net=(gr-tn*COST).dropna(); net=net[net.index>='2008-01-01']
    sc,_=vol_target(net); return sc.dropna()
def pos_map(mp,summer=True):
    p=pd.Series(0.0,index=idx); sm=np.isin(idx.month,range(4,11)) if summer else np.ones(len(idx),bool)
    for d,sgn in mp.items(): p[sm&(idx.dayofweek==d)]=sgn
    return p
if __name__=='__main__':
    # exact WNGSR season
    keep=np.zeros(len(idx),bool)
    for y in idx.year.unique():
        apr=pd.Timestamp(y,4,1); ft=apr+pd.Timedelta(days=(3-apr.dayofweek)%7)
        ob=pd.Timestamp(y,10,31); lt=ob-pd.Timedelta(days=(int(ob.dayofweek)-3)%7)
        keep|=np.asarray(idx>=ft)&np.asarray(idx<=lt)
    pe=pos_map({2:-1.,3:-1.,4:1.}); pe[~keep]=0.0
    print('EXACT season:',{k:round(v,2) for k,v in full_stats(pipeline(pe)).items() if k!='yearly'})
    # vol-regime sizing on base book
    nb=pipeline(pos_map({2:-1.,3:-1.,4:1.}))
    thr=lr.rolling(90).std().shift(1)*2.5
    pb=pos_map({2:-1.,3:-1.,4:1.}).mask(lr.abs()>thr,0.0)
    gr=pb*lr.shift(-1); tn=pb.diff().abs(); tn.iloc[0]=abs(pb.iloc[0])
    nb_raw=(gr-tn*COST).dropna(); nb_raw=nb_raw[nb_raw.index>='2008-01-01']
    sr63=nb_raw.rolling(63).mean()/nb_raw.rolling(63).std()*np.sqrt(252)
    for cap in (2.0,1.5,1.0):
        sc,_=vol_target(nb_raw*(sr63.shift(1)/1.0).clip(lower=0,upper=cap).fillna(0))
        print(f'VOLREGIME cap{cap}:',{k:round(v,2) for k,v in full_stats(sc.dropna()).items() if k!='yearly'})
    # Tue-long standalone (scan survivor t=3.3 pre-filter)
    r=pipeline(pos_map({1:1.0})); st=full_stats(r); h1,h2=halves_sr(r)
    print('TUE-long standalone:',{k:round(v,2) for k,v in st.items() if k!='yearly'},f'H1 {h1:.2f} H2 {h2:.2f}')
