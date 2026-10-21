import pandas as pd, numpy as np
# exact: ex = y/252 - 7*dy - tb3/252 ; long when y.diff(252)<0 ; net = rf + size*(ex) ; vt10 cap2
tb3 = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DTB3.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
dbaa = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DBAA.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
y = dbaa
rf_d = tb3.reindex(y.index).ffill()/252.0
ex = (y/252.0 - 7.0*y.diff()) - rf_d
c = pd.Series(np.where(y.diff(252)<0, ex, 0.0), index=y.index)
net = rf_d + c
vol = net.expanding(60).std().shift(1)*np.sqrt(252)
size = (0.10/vol.replace(0,np.nan)).clip(0,2.0).fillna(0.0)
pos = size.shift(1).fillna(0.0)
ret = net*pos
ret = ret[ret.index>='2008-01-01']
sr = ret.mean()/ret.std()*np.sqrt(252)
print(f"A1credit SYNTH rebuild 2008+: SR {sr:.2f} ann {ret.mean()*252*100:.1f}%")
# on real LQD: same gate/size but real ETF excess return
lqd = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/LQD.csv',index_col=0,parse_dates=True)['close'].astype(float).sort_index()
r_lqd = lqd.pct_change().dropna()
real_net = rf_d.reindex(r_lqd.index).ffill() + pd.Series(np.where(y.diff(252).reindex(r_lqd.index).fillna(False), r_lqd - rf_d.reindex(r_lqd.index).ffill(), 0.0), index=r_lqd.index)
vol2 = real_net.expanding(60).std().shift(1)*np.sqrt(252)
size2 = (0.10/vol2.replace(0,np.nan)).clip(0,2.0).fillna(0.0)
ret2 = (real_net*size2.shift(1).fillna(0.0))
ret2 = ret2[ret2.index>='2008-01-01']
sr2 = ret2.mean()/ret2.std()*np.sqrt(252)
print(f"A1credit REAL-LQD rebuild 2008+: SR {sr2:.2f} ann {ret2.mean()*252*100:.1f}%")
