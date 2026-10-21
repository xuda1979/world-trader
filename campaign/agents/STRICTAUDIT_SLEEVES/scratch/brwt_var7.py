import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.harness.util import vol_target as hvt
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
base='/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/'
# lb10 got corr 0.999889 with z1.0, min 2000: try also 2008 truncation & check brwt7 warmup: file first row 2008-01-03 NaN? first valid?
f7 = pd.read_csv(base+'brwt7.csv', parse_dates=['date']).set_index('date')['ret']
f7 = pd.to_numeric(f7, errors='coerce')
print("brwt7 first valid:", f7.dropna().index[0].date(), "n_valid:", f7.dropna().shape[0])
# try with z=(sp-MA)/SD where SD is population (ddof=0)?
for ddof in [0,1]:
    z=(sp-sp.rolling(7,min_periods=7).mean())/sp.rolling(7,min_periods=7).std(ddof=ddof).replace(0,np.nan)
    pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
    ret=sp.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=(gr-tup*6e-4); net=net[net.index>='2008-01-01']
    scaled=hvt(net)
    j=pd.concat([scaled.rename('r'),f7.rename('f')],axis=1,sort=True).dropna()
    print(f"lb7 z1.0 ddof{ddof} 2008: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.5f}")
# try full-sample (2000) for brwt7 too
z=(sp-sp.rolling(7,min_periods=7).mean())/sp.rolling(7,min_periods=7).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp.diff().shift(-1)
gr=pos*ret; tup=pos.diff().abs()/2.0
net=(gr-tup*6e-4).dropna()
scaled=hvt(net)
j=pd.concat([scaled.rename('r'),f7.rename('f')],axis=1,sort=True).dropna()
print(f"lb7 z1.0 full: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.5f}")
# brwt10 2008-truncated?
f10 = pd.read_csv(base+'brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
z=(sp-sp.rolling(10,min_periods=10).mean())/sp.rolling(10,min_periods=10).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp.diff().shift(-1)
gr=pos*ret; tup=pos.diff().abs()/2.0
net=(gr-tup*6e-4); net=net[net.index>='2008-01-01']
scaled=hvt(net)
j=pd.concat([scaled.rename('r'),f10.rename('f')],axis=1,sort=True).dropna()
print(f"lb10 z1.0 2008-trunc vs brwt10_2000file: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.5f}")
