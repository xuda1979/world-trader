import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
# check whether file = sp.diff().shift(-1)*pos with pos from a DIFFERENT z (with NaN-guard?) on 2020-03-19:
# file ret on 2020-03-19 = +0.12995 -> that equals pos(2020-03-18)*spread_diff(03-18->03-19)
print("spread diff 03-18->03-19:", sp.loc['2020-03-19']-sp.loc['2020-03-18'])
print("implied pos on 03-18:", f10.loc['2020-03-19']/(sp.loc['2020-03-19']-sp.loc['2020-03-18']))
# For repro: pos(03-18) was 0 since z(03-17)=-0.265 (between bands) -> flat.
# What z lookback gives pos=1 (long, z<-1.5) at 03-18?
for lb in [7,10,15,21,30,63]:
    z=(sp-sp.rolling(lb,min_periods=lb).mean())/sp.rolling(lb,min_periods=lb).std()
    print(f"lb{lb}: z(03-17)={z.loc['2020-03-17']:+.3f} z(03-18)={z.loc['2020-03-18']:+.3f}")
