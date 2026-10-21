import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
from campaign.harness.data import fred
BR=fred('brent').dropna(); WT=fred('wti').dropna()
sp=(np.log(BR)-np.log(WT)).dropna()
f10 = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f10 = pd.to_numeric(f10, errors='coerce')
# maxdiff at 2020-03-19 file 0.13 -> look at spread then; maybe different data source (FRED updated brent?)
print("spread on 2020-03-19:", sp.loc['2020-03-16':'2020-03-23'])
# z event: file had big return on 2020-03-19, repro zero => position differs -> z crossed?
z10 = (sp-sp.rolling(10,min_periods=10).mean())/sp.rolling(10,min_periods=10).std()
print(z10.loc['2020-03-10':'2020-03-23'])
