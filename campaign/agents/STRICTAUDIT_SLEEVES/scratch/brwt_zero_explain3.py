import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
# hysteresis explanation: enter |z|>1.0, exit when z crosses back through |z|<1.0?
# Exact repro: pos[z<-1.0]=1, pos[z>1.0]=-1, else 0 (NO hysteresis — position resets to 0 when 1<|z|... wait no: only sets on z<-1 or z>1; else 0).
# So pos(t)=0 whenever |z(t)|<1. Zero-run = consecutive days with |z|<1. But max|z|=1.47>1? Then pos nonzero that day...
# UNLESS the run in the FILE is measured after vt scaling (tiny-but-nonzero returns) — no, zeros are exact.
# Check: does a position entry at z crossing -1.0 produce zero ret on those days because ret=sp.diff().shift(-1) is tiny but not zero? File shows exact zeros.
# => the file zeros must be days where pos(t)=0. Rebuild pos and compare directly:
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna(); sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp.diff().shift(-1)
gr=(pos*ret)
f15 = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
# compare file zeros to pos==0 days
zz = (f15.abs()<1e-12)
pz = (pos.reindex(f15.index).abs()<1e-12)
agree = (zz==pz).mean()
print(f"file-zero-day == pos-zero-day agreement: {agree:.4f}")
run = pd.date_range('2016-05-02', periods=33)
print("2016 run: pos==0 all:", bool((pos.reindex(run).abs()<1e-12).all()))
zzz = z.reindex(run)
print("max|z| in 2016 run:", zzz.abs().max().round(3), "-> crossing above 1 happens on:", zzz.abs()[zzz.abs()>1.0].index.strftime('%Y-%m-%d').tolist())
