import pandas as pd, numpy as np
# A1credit formula: ex = (y/252 - 7*dy) - rf ; pos shift(1) when 252d yield change < 0
dbaa = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DBAA.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
tb = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DTB3.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0 if False else None
rf = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS1.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
y = dbaa
ex = (y/252.0 - 7.0*y.diff()) - rf.reindex(y.index).ffill()
sig = (y.diff(252) < 0)
exdf = ex[sig.reindex(ex.index).fillna(False)]
def stats(r, name):
    r = r.dropna()
    sr = r.mean()/r.std()*np.sqrt(252)
    print(f"{name}: SR {sr:.2f} ann {r.mean()*252*100:.1f}% n={len(r)}")
stats(exdf[exdf.index>='2008-01-01'], "A1credit on SYNTH BAA (2008+)")
# now on real LQD total return
lqd = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/LQD.csv',index_col=0,parse_dates=True)['close'].astype(float).sort_index()
r_lqd = lqd.pct_change().dropna()
rf_d = rf.reindex(r_lqd.index).ffill()
ex_real = r_lqd - rf_d/252.0
ex_real_gate = ex_real[sig.reindex(ex_real.index).fillna(False)]
stats(ex_real_gate[ex_real_gate.index>='2008-01-01'], "A1credit gate on REAL LQD (2008+)")
