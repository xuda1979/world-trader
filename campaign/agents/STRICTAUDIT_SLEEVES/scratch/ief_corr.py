import pandas as pd, numpy as np
# Independent instrument-reality check: synth 2y TR and synth 10y TR vs real IEF (twelvedata)
ief = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/IEF.csv',index_col=0,parse_dates=True)['close']
ief.index = pd.to_datetime(ief.index)
ief = ief.astype(float).sort_index()
r_ief = ief.pct_change().dropna()
y2 = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
y10 = pd.to_numeric(pd.read_csv('/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS10.csv',index_col=0,parse_dates=True).iloc[:,0],errors='coerce').dropna().sort_index()/100.0
tr2 = (-1.9*y2.diff()+y2/252.0).dropna()
tr10 = (-8.5*y10.diff()+y10/252.0).dropna()
for nm, tr in [('synth2y',tr2),('synth10y',tr10)]:
    j = pd.concat([tr.rename('synth'), r_ief.rename('ief')],axis=1,sort=True).dropna()
    print(f"{nm} vs IEF daily-ret corr: n={len(j)} corr={j['synth'].corr(j['ief']):.3f}")
