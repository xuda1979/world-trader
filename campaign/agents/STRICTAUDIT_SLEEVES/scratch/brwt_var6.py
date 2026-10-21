import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.harness.util import vol_target as hvt
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
base='/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/'
# refine lb7/lb5: maybe z-band 1.0 but different cost, or slightly different vt, or min_start 2008 truncation & vt differently
for lb, fnm in [(7,base+'brwt7.csv'), (5,base+'brwt5.csv')]:
    f = pd.read_csv(fnm, parse_dates=['date']).set_index('date')['ret']
    f = pd.to_numeric(f, errors='coerce')
    for ms in ['2008-01-01','2000-01-01']:
      for cost in [6,4,2,8]:
        for vt_t in [0.08,0.10,0.12]:
            z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
            pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
            ret=sp.diff().shift(-1)
            gr=pos*ret; tup=pos.diff().abs()/2.0
            net=(gr-tup*cost*1e-4)
            net=net[net.index>=ms] if ms!='2000-01-01' else net.dropna()
            scaled=hvt(net, target=vt_t)
            j=pd.concat([scaled.rename('r'),f.rename('f')],axis=1,sort=True).dropna()
            c=j['r'].corr(j['f'])
            if c>0.995: print(f"lb{lb} ms={ms} cost={cost} vt={vt_t}: corr={c:.6f} maxdiff={(j['r']-j['f']).abs().max():.5f}")
print("done")
