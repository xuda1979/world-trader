import pandas as pd, numpy as np, sys, importlib.util, io, contextlib
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/harness")
spec = importlib.util.spec_from_file_location('cs','/Users/daxu/software/world-trader/campaign/scripts/a1_carry_seasonal.py')
cs = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(cs)
sleeve = cs.sleeve
f = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv', parse_dates=['date']).set_index('date')['ret']
j = pd.concat([sleeve.rename('r'), f.rename('f')], axis=1, sort=True).dropna()
d=(j['r']-j['f']).abs()
print(f"carryv2 vs a1_carry_seasonal.sleeve (2008 version): n={len(j)} corr={j['r'].corr(j['f']):.6f} max|d|={d.max():.3e}")
