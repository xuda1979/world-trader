import pandas as pd, numpy as np, sys, importlib.util
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
net = bb.run(lookback=15, buy_z=1.5, cost=6)
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
scaled,_ = vol_target(net)
# E1 file: full history (no 2008 truncation)
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv', parse_dates=['date']).set_index('date')['ret']
j = pd.concat([scaled.rename('repro'), f.rename('file')], axis=1, sort=True).dropna()
print(f"brwt15: n={len(j)} corr={j['repro'].corr(j['file']):.8f} max|diff|={(j['repro']-j['file']).abs().max():.3e}")
# COORD brwt10/7/5 = same recipe with lookback 10/7/5, min_start 2008
for lb, path in [(10,'/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv'),
                 (7,'/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt7.csv'),
                 (5,'/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt5.csv')]:
    try:
        n2 = bb.run(lookback=lb, buy_z=1.5, cost=6, min_start='2000-01-01' if '2000' in path else '2008-01-01')
        s2,_ = vol_target(n2)
        f2 = pd.read_csv(path, parse_dates=['date']).set_index('date')['ret']
        j2 = pd.concat([s2.rename('repro'), f2.rename('file')], axis=1, sort=True).dropna()
        print(f"brwt{lb}: n={len(j2)} corr={j2['repro'].corr(j2['file']):.6f} max|diff|={(j2['repro']-j2['file']).abs().max():.3e} first file {f2.dropna().index[0]}")
    except Exception as e:
        print(f"brwt{lb}: ERR {e}")
