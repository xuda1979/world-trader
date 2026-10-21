import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
from campaign.harness.util import vol_target as hvt
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
base='/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/'
f7 = pd.read_csv(base+'brwt7.csv', parse_dates=['date']).set_index('date')['ret']
f7 = pd.to_numeric(f7, errors='coerce')
# ddof1 + 2008 helps (0.9993). Try min_start 2008-01-01 in run() which also truncates the SPREAD series before z (like run() does) — I did net truncation only. Try truncating sp first:
for ms in ['2007-01-01','2008-01-01']:
    sp_t = sp[sp.index>=ms]
    z=(sp_t-sp_t.rolling(7,min_periods=7).mean())/sp_t.rolling(7,min_periods=7).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp_t.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
    ret=sp_t.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=(gr-tup*6e-4).dropna()
    scaled=hvt(net)
    j=pd.concat([scaled.rename('r'),f7.rename('f')],axis=1,sort=True).dropna()
    print(f"lb7 sp-trunc {ms}: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.5f} n={len(j)}")
# also vt via B2 gates (rolling not expanding, no shift1)
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target as gvt
sp_t = sp[sp.index>='2008-01-01']
z=(sp_t-sp_t.rolling(7,min_periods=7).mean())/sp_t.rolling(7,min_periods=7).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp_t.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp_t.diff().shift(-1)
gr=pos*ret; tup=pos.diff().abs()/2.0
net=(gr-tup*6e-4).dropna()
for vtname, vt in [('B2gates',gvt),('harness',hvt)]:
    scaled = vt(net)[0] if vtname=='B2gates' else vt(net)
    j=pd.concat([scaled.rename('r'),f7.rename('f')],axis=1,sort=True).dropna()
    print(f"lb7 trunc2008 vt={vtname}: corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.5f}")
