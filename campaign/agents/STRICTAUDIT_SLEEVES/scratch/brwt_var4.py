import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
fn = f10.dropna()
# the first VALID row 2000-03-30 equals brwt15 repro start+60? brwt15 first nonzero 2000-04-10.
# brwt15 repro first index 2000-01-05 (net). With vt min60 -> first scaled 2000-03-30! (60 obs later)
# So file likely = vt-scaled with SAME convention: vt starts at row 60.
# The file rows BEFORE 2000-03-30 are NaN (59 rows) — but where did the strategy signal come from before?
# Likely generator: net = run(min_start='2000-01-01'); scaled with vt60; file only kept from first scaled value?
# BUT corr is still 0.725 -> positions differ. Try reversing: long z>1.5, short z<-1.5?? or spread reversed?
net_rev = None
import importlib.util
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
from campaign.harness.util import vol_target as hvt
# WTI-Brent reversed spread
BRs, WTs = BR.align(WT, join='inner')
sp2 = np.log(WTs)-np.log(BRs)
for lb in [10]:
    z=(sp2-sp2.rolling(lb,min_periods=lb).mean())/sp2.rolling(lb,min_periods=lb).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp2.index); pos[z<-1.5]=1.0; pos[z>1.5]=-1.0
    ret=sp2.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=(gr-tup*6e-4).dropna()
    scaled=hvt(net)
    j=pd.concat([scaled.rename('r'),f10.rename('f')],axis=1,sort=True).dropna()
    print(f"reversed spread lb{lb}: n={len(j)} corr={j['r'].corr(j['f']):.6f}")
# maybe z bands 2.0?
for bz in [1.0,2.0,2.5]:
    sp3=(np.log(BR)-np.log(WT)).dropna()
    z=(sp3-sp3.rolling(10,min_periods=10).mean())/sp3.rolling(10,min_periods=10).std().replace(0,np.nan)
    pos=pd.Series(0.0,index=sp3.index); pos[z<-bz]=1.0; pos[z>bz]=-1.0
    ret=sp3.diff().shift(-1)
    gr=pos*ret; tup=pos.diff().abs()/2.0
    net=(gr-tup*6e-4).dropna()
    scaled=hvt(net)
    j=pd.concat([scaled.rename('r'),f10.rename('f')],axis=1,sort=True).dropna()
    print(f"lb10 z{bz}: n={len(j)} corr={j['r'].corr(j['f']):.6f} maxdiff={(j['r']-j['f']).abs().max():.4f}")
