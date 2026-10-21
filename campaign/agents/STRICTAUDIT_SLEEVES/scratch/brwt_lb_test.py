import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
from campaign.harness.util import vol_target as hvt
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target as gvt
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv', parse_dates=['date']).set_index('date')['ret']
f = pd.to_numeric(f, errors='coerce').dropna()
# scan lookback for best corr to the brwt10 file
best = []
net_lb10 = bb.run(lookback=10, buy_z=1.5, cost=6, min_start='2000-01-01')
for lb in range(3, 31):
    net = bb.run(lookback=lb, buy_z=1.5, cost=6, min_start='2000-01-01')
    for vt, tag in [(gvt,'B2'),(hvt,'H')]:
        scaled = vt(net)[0] if tag=='B2' else vt(net)
        j = pd.concat([scaled.rename('r'), f.rename('f')],axis=1,sort=True).dropna()
        c = j['r'].corr(j['f'])
        best.append((c, lb, tag))
best.sort(reverse=True)
print("top5:", best[:5])
# maybe cost param different? or buy_z?
net = bb.run(lookback=10, buy_z=1.5, cost=6, min_start='2000-01-01')
j = pd.concat([gvt(net)[0].rename('r'), f.rename('f')],axis=1,sort=True).dropna()
i = (j['r']-j['f']).abs().idxmax()
print("maxdiff at", i.date(), "repro", j['r'].loc[i], "file", j['f'].loc[i])
print("early rows: file head:\n", f.head(70).tail(10))
print("repro head:\n", gvt(net)[0].head(70).tail(10))
