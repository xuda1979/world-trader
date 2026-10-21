import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
fn = f10.dropna()
# file first valid 2000-03-30. 2000-01-04 + 60 business days?
print("brent idx 59:", BR.index[59].date(), "idx 60:", BR.index[60].date())
# Maybe the COORD variant uses a DIFFERENT spread source: WTI-Brent reversed + rev15 in COORD sleeve dir "WTI-Brent_rev.csv"
alt = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/WTI-Brent_rev.csv', parse_dates=['date']).set_index('date')['ret']
print("WTI-Brent_rev file:", alt.shape, alt.dropna().index[0] if len(alt) else None)
brent_wti = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brent_wti_spread.csv', parse_dates=['date']).set_index('date').iloc[:,0]
print("brent_wti_spread file:", brent_wti.shape, brent_wti.dropna().index[0])
# compare spread file to fred spread
sp=(np.log(BR)-np.log(WT)).dropna()
j = pd.concat([sp.rename('fred'), brent_wti.rename('file')], axis=1, sort=True).dropna()
print(f"spread corr n={len(j)}: {j['fred'].corr(j['file']):.6f} maxdiff={(j['fred']-j['file']).abs().max():.3e}")
