import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
# verify the two 33d runs of brwt15 are |z|<1.5 (band gate flat)
f15 = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
zabs=(f15.abs()<1e-12)
grp=(zabs!=zabs.shift()).cumsum()
runs=[]
for k,g in zabs.groupby(grp):
    if bool(g.iloc[0]) and len(g)>=25:
        runs.append((str(g.index[0].date()),len(g)))
print("brwt15 zero-runs >=25d:", runs[:6])
for d0,ln in runs[:4]:
    dd = pd.date_range(d0, periods=ln)
    zz = z.reindex(dd)
    print(f"  run {d0} len{ln}: max|z|={zz.abs().max():.3f} (all<1.5: {bool((zz.abs()<1.5).all())})")
