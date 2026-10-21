import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
from campaign.harness.data import fred
WT=fred('wti').dropna(); BR=fred('brent').dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
# file NaN rows: 59 at head per mech check. The file starts 2000-01-05 with NaN, first numbers around 2000-06?
fn = f10.dropna()
print("file valid rows:", len(fn), "first:", fn.index[0].date(), "last:", fn.index[-1].date())
print("head:\n", fn.head(15))
# file's first valid rows are June 2000 -> lookback warmup 125 days? FRED brent starts 2000-01-04? so start+~125bd
print("brent first:", BR.index[0].date(), "wti first:", WT.index[0].date())
# 2000-01-04 + 126 business days:
print("brent idx 126:", BR.index[126].date())
# hypothesis: brent (not wti) has later start; warmup = 60d vt min + something
