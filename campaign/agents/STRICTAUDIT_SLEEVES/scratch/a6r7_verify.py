import pandas as pd, numpy as np, sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
# a6r7 E1: synthetic 2y TR from DGS2, K=378 cadence 42, T+1, 6bps, vt12 cap5
DGS2='/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/DGS2.csv'
y=pd.read_csv(DGS2,index_col=0,parse_dates=True).iloc[:,0]
y=pd.to_numeric(y,errors='coerce').dropna().sort_index()
y=y/100.0
DUR=1.9
tr=(-DUR*y.diff()+y/252.0).dropna()
K,CAD,CAP=378,42,5.0
sig=(tr.rolling(K).mean()>0).astype(float)
W=sig.iloc[::CAD].reindex(tr.index).ffill().fillna(0.0)
gross=(W.shift(1)*tr)
turn=(W.shift(1)-W.shift(2)).abs().fillna(0.0)
net=(gross-turn*6e-4).dropna()
VT=0.12
lev=(VT/np.sqrt(252)/net.expanding(60).std().shift(1)).clip(0,CAP).fillna(0.0)
r=(net*lev).dropna()
f=pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',parse_dates=['date']).set_index('date')['ret']
j=pd.concat([r.rename('r'),f.rename('f')],axis=1,sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"a6r7: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
