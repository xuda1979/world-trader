import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
spd = sp.diff()
common = f10.index.intersection(spd.index)
spd_c = spd.reindex(common); f_c = f10.reindex(common)
bigmask = np.abs(spd_c.values)>0.02
pos_impl = (f_c.values/spd_c.values)[bigmask]
dates_big = common[bigmask]
best=(-1,)
for lb in range(3,41):
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    zv = z.reindex(common).values
    for enter, exit_ in [(1.5,1.5),(2,1),(2,0.5),(2.5,0.5),(1.5,0.5),(2,1.5),(3,1),(3,2)]:
        pos=np.zeros(len(common)); cur=0.0
        for i in range(len(common)):
            v=zv[i]
            if cur==0:
                if v==v and v<-enter: cur=1.0
                elif v==v and v>enter: cur=-1.0
            else:
                if cur==1 and v==v and v>-exit_: cur=0.0
                elif cur==-1 and v==v and v<exit_: cur=0.0
            pos[i]=cur
        pm = np.abs(pos_impl - pos[bigmask])
        frac = float((pm<0.01).mean())
        if frac>best[0]: best=(frac,lb,enter,exit_)
print("best: frac=%.4f lb=%d enter=%.2f exit=%.2f" % best)
