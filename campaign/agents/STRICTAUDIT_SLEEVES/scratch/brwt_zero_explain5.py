import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
# Key insight: the exact repro used B2 gates.vol_target (rolling 60d std, NO shift). During flat/vt-capped periods
# scale ~ small but nonzero -> returns would NOT be exactly zero... yet file rows are exactly 0.0.
# BUT WAIT: brwt15's FILE zeros come in runs where the REBUILT series (which matched corr=1.0, maxdiff 1e-16 on ALL 6547 rows)
# must ALSO be exactly zero. So in the rebuild, pos(t)*ret(t+1)=0 exactly there. Let me verify by rebuilding and
# printing the rebuilt values on the run.
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna(); sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp.diff().shift(-1)
gr=(pos*ret); tup=pos.diff().abs()/2.0
net=(gr-tup*6e-4).dropna()
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
scaled,_=vol_target(net)
run = pd.date_range('2016-05-02','2016-06-03')
sv = scaled.reindex(run)
print("rebuilt scaled values on 2016-05-02..06-03 (max|v|):", sv.abs().max())
print("nonzero count:", int((sv.abs()>0).sum()))
f15 = pd.to_numeric(pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce')
print("file same window nonzero count:", int((f15.reindex(run).abs()>0).sum()))
