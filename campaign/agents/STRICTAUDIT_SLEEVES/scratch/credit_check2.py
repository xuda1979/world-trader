import pandas as pd, numpy as np
lqd = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/LQD.csv',index_col=0,parse_dates=True)['close'].astype(float).sort_index()
hyg = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/HYG.csv',index_col=0,parse_dates=True)['close'].astype(float().dtype if False else float).sort_index()
r_lqd = lqd.pct_change().dropna(); r_hyg = hyg.pct_change().dropna()
baa = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DBAA.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
tr = (-7.0*baa.diff()+baa/252.0).dropna()
for nm, r in [('LQD',r_lqd),('HYG',r_hyg)]:
    j = pd.concat([tr.rename('synth'), r.rename('real')],axis=1,sort=True).dropna()
    print(f"synth BAA TR vs {nm}: n={len(j)} corr={j['synth'].corr(j['real']):.3f}")
