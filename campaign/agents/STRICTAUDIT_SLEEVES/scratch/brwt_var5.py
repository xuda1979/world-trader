import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.harness.util import vol_target as hvt
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
files = {10:'brwt10_2000.csv', 7:'brwt7.csv', 5:'brwt5.csv', 15:'brwt15'}
base='/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/'
# hypothesis: lb{10,7,5} files use band z=1.0 not 1.5? Or maybe the 2000-file used (z-std over rolling)... try z1.0 for all
for lb, fnm in [(10,base+'brwt10_2000.csv'), (7,base+'brwt7.csv'), (5,base+'brwt5.csv')]:
    f = pd.read_csv(fnm, parse_dates=['date']).set_index('date')['ret']
    f = pd.to_numeric(f, errors='coerce')
    for bz in [0.5,1.0,1.5]:
        z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std().replace(0,np.nan)
        pos=pd.Series(0.0,index=sp.index); pos[z<-bz]=1.0; pos[z>bz]=-1.0
        ret=sp.diff().shift(-1)
        gr=pos*ret; tup=pos.diff().abs()/2.0
        net=(gr-tup*6e-4).dropna()
        scaled=hvt(net)
        j=pd.concat([scaled.rename('r'),f.rename('f')],axis=1,sort=True).dropna()
        print(f"lb{lb} z{bz}: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.4f} n={len(j)}")
