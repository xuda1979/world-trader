import pandas as pd, numpy as np
# Final consolidated per-sleeve stats for verdict table + brwt vt-shift materiality (AUDIT2's finding)
SLEEVES = {
 'brwt15': '../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',
 'brwt10': '../../../agents/COORD/sleeves/brwt10_2000.csv',
 'brwt7':  '../../../agents/COORD/sleeves/brwt7.csv',
 'brwt5':  '../../../agents/COORD/sleeves/brwt5.csv',
 'C5ng':   '../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
 'C5ngsum':'../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
 'A5r2':   '../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',
 'a6r7':   '../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',
 'QAxasts':'../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',
 'carryv2':'../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',
 'dualmom':'../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',
 'XGB1y':  '../../../results/sleeve_library/XGB1y_deploy.csv',
}
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
# vt-shift materiality for brwt & C5ng: rebuild without vt then vt with shift vs without shift
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
sp=sp[sp.index>='2000-01-01']
z=(sp-sp.rolling(15,min_periods=15).mean())/sp.rolling(15,min_periods=15).std().replace(0,np.nan)
pos=pd.Series(0.0,index=sp.index); pos[z<-1.0]=1.0; pos[z>1.0]=-1.0
ret=sp.diff().shift(-1)
gr=pos*ret; tup=pos.diff().abs()/2.0
net=(gr-tup*6e-4).dropna()
def vt_shift(r, shift=True):
    v = r.expanding(60).std()
    if shift: v = v.shift(1)
    lev=(0.10/v*np.sqrt(252) if False else (0.10/(v*np.sqrt(252)))).clip(0,3)
    return (r*lev).dropna()
a = vt_shift(net, shift=False); b = vt_shift(net, shift=True)
print(f"brwt15 raw-engine vt NO-shift SR={a.mean()/a.std()*np.sqrt(252):.3f} vs WITH shift SR={b.mean()/b.std()*np.sqrt(252):.3f}")
