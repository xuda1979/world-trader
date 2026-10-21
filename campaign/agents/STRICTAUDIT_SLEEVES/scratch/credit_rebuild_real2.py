import pandas as pd, numpy as np
# fix: rf daily rate = rf/252 subtracted from daily ex; my synth gave crazy number because rf misindexed? check
dbaa = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DBAA.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
rf = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS1.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
print("DGS1 available from:", rf.index[0].date())
ex = (dbaa/252.0 - 7.0*dbaa.diff()) - rf.reindex(dbaa.index).ffill()
print("ex stats:", ex.describe().round(5).to_dict())
