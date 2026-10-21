import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
# Rebuild EXACT z for brwt15 (z1.0 band per exact repro) and check gate across the long runs:
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
f15 = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
zabs=(f15.abs()<1e-12)
grp=(zabs!=zabs.shift()).cumsum()
for k,g in zabs.groupby(grp):
    if bool(g.iloc[0]) and len(g)>=25:
        d0=g.index[0]; dd=g.index
        # gate: |z(t)|<1 at t (band 1.0) — positions flat
        zz = z.reindex(dd)
        ok = (zz.abs()<1.0).all()
        print(f"run {d0.date()} len{len(g)}: max|z|={zz.abs().max():.3f} all|z|<1.0={bool(ok)}")
