import pandas as pd, numpy as np
# A5r7 independent real-ETF test: 63d momentum of LQD/HYG long when positive (credit momentum core)
lqd = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/LQD.csv',index_col=0,parse_dates=True)['close'].astype(float).sort_index()
hyg = pd.read_csv('/Users/daxu/software/world-trader/tools/quant/data/twelvedata/HYG.csv',index_col=0,parse_dates=True)['close'].astype(float).sort_index()
for nm, p in [('LQD',lqd),('HYG',hyg)]:
    r = p.pct_change().dropna()
    mom = p.pct_change(63).reindex(r.index).ffill()
    pos = (mom>0).astype(float).shift(1).fillna(0.0)
    net = pos*r - pos.diff().abs().fillna(0)*1e-3
    net = net[net.index>='2008-01-01']
    print(f"{nm} 63d momentum long/flat 2008+: SR {net.mean()/net.std()*np.sqrt(252):.2f} ann {net.mean()*252*100:.1f}%")
