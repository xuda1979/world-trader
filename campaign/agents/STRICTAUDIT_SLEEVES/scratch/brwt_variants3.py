import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
from campaign.harness.util import vol_target as hvt

for lb, ms, path in [(10,'2000-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv'),
                     (7,'2008-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt7.csv'),
                     (5,'2008-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt5.csv')]:
    net = bb.run(lookback=lb, buy_z=1.5, cost=6, min_start=ms)
    scaled = hvt(net, target=0.10, min_win=60, lag=1)
    f = pd.read_csv(path, parse_dates=['date']).set_index('date')['ret']
    f = pd.to_numeric(f, errors='coerce')
    j = pd.concat([scaled.rename('repro'), f.rename('file')], axis=1, sort=True).dropna()
    print(f"brwt{lb} harness-vt: n={len(j)} corr={j['repro'].corr(j['file']):.8f} max|diff|={(j['repro']-j['file']).abs().max():.3e}")
