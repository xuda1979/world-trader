import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
# 2020-04: WTI went NEGATIVE (futures). FRED spot WTI? check values
print("WTI FRED 2020-04:", WT.loc['2020-04-15':'2020-04-22'].values)
print("brent 2020-04-20:", BR.loc['2020-04-17':'2020-04-22'].values)
# check if the file's 2020-04-21 value (the -37$ day) is a monster
print("file 2020-04-17..24:")
print(f10.loc['2020-04-17':'2020-04-24'])
print("spread diffs:", sp.diff().loc['2020-04-17':'2020-04-24'])
