import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
tests = [
 (10,'2000-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt10_2000.csv'),
 (7,'2008-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt7.csv'),
 (5,'2008-01-01','/Users/daxu/software/world-trader/campaign/agents/COORD/sleeves/brwt5.csv'),
]
for lb, ms, path in tests:
    net = bb.run(lookback=lb, buy_z=1.5, cost=6, min_start=ms)
    scaled,_ = vol_target(net)
    f = pd.read_csv(path, parse_dates=['date']).set_index('date')['ret']
    f = pd.to_numeric(f, errors='coerce')
    j = pd.concat([scaled.rename('repro'), f.rename('file')], axis=1, sort=True).dropna()
    if len(j)==0:
        # file has NaN head; align on repro index
        f2 = f.reindex(scaled.index)
        both = pd.concat([scaled.rename('repro'), f2.rename('file')],axis=1)
        both_nonnan = both.dropna()
        print(f"brwt{lb}: n_nonnan={len(both_nonnan)} corr={both_nonnan['repro'].corr(both_nonnan['file']):.8f} max|diff|={(both_nonnan['repro']-both_nonnan['file']).abs().max():.3e}  (file NaN rows: {f2.isna().sum()})")
    else:
        print(f"brwt{lb}: n={len(j)} corr={j['repro'].corr(j['file']):.8f} max|diff|={(j['repro']-j['file']).abs().max():.3e}")
