import pandas as pd, numpy as np
# Confirm A5r4 is OUT of the 12-sleeve pool (already known from JSON) AND check A5r2 vs A5r4 corr
a = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',parse_dates=['date']).set_index('date')['ret']
b = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/A5_vol_cond/sleeves/A5_r4_vt15_contango.csv',parse_dates=['date']).set_index('date')['ret']
j = pd.concat([a.rename('r2'), b.rename('r4')],axis=1,sort=True).dropna()
print(f"A5r2-A5r4 corr={j['r2'].corr(j['r4']):.4f} (raw, n={len(j)})")
print("A5r4 in STRICTTRADE pool?", 'A5r4' in open('/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE.json').read())
# A5r7 & A1credit exclusion check
js = open('/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE.json').read()
print("A5r7 excluded?", 'A5r7' in js.split('excluded')[1])
