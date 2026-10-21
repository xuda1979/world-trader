import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader')
spec = importlib.util.spec_from_file_location('bb','/Users/daxu/software/world-trader/campaign/scripts/backtest_brwt_spread_rev15.py')
bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/B2_highfreq')
from gates import vol_target
net = bb.run(lookback=15, buy_z=1.5, cost=6, min_start='2000-01-01')
scaled, sc = vol_target(net)
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv', parse_dates=['date']).set_index('date')['ret']
j = pd.concat([scaled.rename('repro'), f.rename('file')], axis=1, sort=True).dropna()
print(f"brwt15 (min_start 2000): n={len(j)} corr={j['repro'].corr(j['file']):.8f} max|diff|={(j['repro']-j['file']).abs().max():.3e}")
# check where file starts having nonzero
fnz = f[f.abs()>1e-12]
print("file first nonzero:", fnz.index[0], " repro first:", scaled.index[0])
# 59 NaNs in brwt10 file (vt warmup) — replicate: file may store empty cells during vt warmup
# Try: maybe E1 used harness vt10 cap3 vs B2 cap3? gates.vol_target caps at 3.0. Check scale dist
print("scale max:", sc.max(), "scale cap check")
# where does max|diff| occur
i = (j['repro']-j['file']).abs().idxmax()
print("maxdiff at", i.date(), "repro", j['repro'].loc[i], "file", j['file'].loc[i])
# corr within 2008+
j08 = j[j.index>='2008-01-01']
print(f"corr 2008+: {j08['repro'].corr(j08['file']):.6f}")
