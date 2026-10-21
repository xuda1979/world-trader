import pandas as pd, numpy as np, sys, importlib.util
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
spec = importlib.util.spec_from_file_location('a5r2m','/Users/daxu/software/world-trader/campaign/scripts/a5_r2_rate_shock_contango.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
net = m.net
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',parse_dates=['date']).set_index('date')['ret']
j = pd.concat([net.rename('r'), f.rename('f')],axis=1,sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"A5r2: n={len(j)} corr={j['r'].corr(j['f']):.8f} max|d|={d.max():.3e} exact={(d<1e-12).sum()}")
print("A5r2 sleeves dir files:")
import glob
print(glob.glob('/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/*'))
