import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
# brwt April 2020: negative WTI spot print - how do files handle it?
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f15 = pd.read_csv('../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',parse_dates=['date']).set_index('date')['ret']
print("E1 brwt15 2020-04-17..24:", f15.loc['2020-04-17':'2020-04-24'].round(4).to_dict())
# log of negative wti => NaN; check sp around 2020-04-20
print("sp values 2020-04-16..22:", sp.loc['2020-04-16':'2020-04-22'].round(4).to_dict())
