import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target as gvt
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
base='/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/'
files = {'brwt10_2000.csv': ('2000-01-01',10), 'brwt7.csv': ('2008-01-01',7), 'brwt5.csv': ('2008-01-01',5)}
for fnm,(ms,lb) in files.items():
    f = pd.read_csv(base+fnm, parse_dates=['date']).set_index('date')['ret']
    f = pd.to_numeric(f, errors='coerce')
    sp_t = sp[sp.index>=ms]
    z=(sp_t-sp_t.rolling(lb,min_periods=lb).mean())/sp_t.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp_t.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
    ret=sp_t.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=(gr-tup*6e-4).dropna()
    scaled,_=gvt(net)
    j=pd.concat([scaled.rename('r'),f.rename('f')],axis=1,sort=True).dropna()
    d=(j['r']-j['f']).abs()
    print(f"{fnm} z1.0 trunc{ms[:4]} B2vt: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={ (d<1e-12).sum()}")
