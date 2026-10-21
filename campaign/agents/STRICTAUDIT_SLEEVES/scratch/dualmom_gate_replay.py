import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality')
from campaign.harness import data as D
px = D.closes()
ff = D.ff_factors()
mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
ma = mkt.rolling(200, min_periods=200).mean()
g = pd.Series(np.where(mkt > ma*1.03, 1.0, np.where(mkt < ma*0.97, 0.0, np.nan)), index=mkt.index)
# month-ends of the dualmom CSV
f = pd.read_csv('../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',parse_dates=['date']).set_index('date')['ret']
run = f.loc['2022-02-02':'2023-01-31']
# gate value at month-ends preceding/at the run
mes = pd.date_range('2021-12-01','2023-02-28',freq='ME')
gv = g.reindex(mes).ffill()
print("gate at month-ends 2021-12..2023-02:")
print(gv.to_string())
