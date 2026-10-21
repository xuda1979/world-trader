import pandas as pd, numpy as np
# brwt lookback-ensemble: correlation of z-signal overlap. lb5/7/10/15 with band1.0: overlapping gates
# Also: how much do the 4 lookbacks agree day by day (same position)?
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna(); sp=sp[sp.index>='2008-01-01']
P={}
for lb in [5,7,10,15]:
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
    P[lb]=pos
Pd=pd.DataFrame(P)
agree = {}
import itertools
for a,b in itertools.combinations([5,7,10,15],2):
    agree[f"{a}-{b}"] = round(float((Pd[a]==Pd[b]).mean()),3)
print("position-agreement across brwt lookbacks (2008+):", agree)
