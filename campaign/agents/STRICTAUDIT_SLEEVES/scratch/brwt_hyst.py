import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
# implied daily positions from file: pos(t) = ret(t+1)/spdiff(t+1) (where |spdiff| big)
spd = sp.diff()
pos_impl = (f10/spd.shift(0)).shift(-1)  # careful: file ret(t) = pos(t-1)*spd(t); pos_impl(t-1)=ret(t)/spd(t)
pos_impl = f10.shift(-1)/spd  # ret(t)=pos(t)*spd(t+1) => pos(t)=ret(t)/spd(t+1)
# clean
pos_impl = pos_impl[np.abs(spd)>0.02]
# estimate z at decision times: for lb in 5..30 find best match
from itertools import product
best=(9,None)
for lb in range(3,41):
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    # reconstruct positions with hysteresis enter/exit candidates: simple: match fraction
    for enter, exit_ in [(1.5,1.5),(2,1),(2,0.5),(2.5,0.5),(1.5,0.5),(2,1.5)]:
        pos=pd.Series(0.0,index=sp.index); cur=0.0
        for t in sp.index:
            v=z.get(t,np.nan)
            if cur==0:
                if v<-enter: cur=1.0
                elif v>enter: cur=-1.0
            else:
                if cur==1 and v>-exit_: cur=0.0
                elif cur==-1 and v<exit_: cur=0.0
            pos[t]=cur
        ret=pos*spd.shift(-1)
        j=pd.concat([ret.rename('r'),f10.rename('f')],axis=1,sort=True).dropna()
        # positions match on big-move days
        pm = (pos_impl - pos.reindex(pos_impl.index)).abs()
        frac = (pm<0.01).mean()
        corr = j['r'].corr(j['f'])
        if frac>best[0]:
            best=(frac,lb,enter,exit_,corr)
print("best:", best)
