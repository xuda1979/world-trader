import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
# The exact repro matched (corr 1.0) with band 1.0 and NO hysteresis: pos in {-1,0,1} directly from z each day.
# But then a "zero-run" in FILE = consecutive exact-zero returns. If pos!=0 on day t, ret= pos*sp.diff(t+1) rarely exactly 0.
# My pos zero agreement only 0.75 => the committed file was built with pos from band 1.5?? but exact repro used 1.0 and matched 6547/6547!
# Contradiction => the 33d "zero runs" in FILE need explanation. Since exact rebuild matched EVERY row, the runs must
# be days where pos(t)*sp.diff(t+1)==0 exactly, i.e. sp.diff(t+1)==0 (spread unchanged) OR pos==0.
# Check: in the 2016 run, was sp.diff()==0 on those days?
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna(); sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
run = pd.date_range('2016-05-02', periods=33)
d1 = sp.diff().shift(-1).reindex(run)
pp = pos.reindex(run)
contribution = pp*d1
print("2016 run: days pos!=0:", int((pp!=0).sum()))
print("of those, sp.diff(t+1)==0:", int(((pp!=0)&(d1.abs()<1e-12)).sum()))
print("nonzero pos with zero spread-diff dates:", ((pp!=0)&(d1.abs()<1e-12)).index.strftime('%Y-%m-%d').tolist())
