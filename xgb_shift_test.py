import pandas as pd, numpy as np
R='/Users/daxu/software/world-trader'
m = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv', index_col=0, parse_dates=True)
s = m.iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
# test all shifts k: daily value in month p = source value at month p-k
for k in range(-3, 4):
    m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M') + k)
    built = pd.Series(per.map(m2).astype(float).values, index=x.index)
    ok = built.notna()
    diff = (x[ok] - built[ok]).abs()
    print(f"shift {k:+d}: n={ok.sum():4d} max|d|={diff.max():.4e} exact={(diff<=1e-12).sum():4d}")
# the audit2 claim: pnl(m) spread on month m's days. Why mismatch? maybe source updated since?
# check source file mtime vs daily file mtime
import os, datetime
for p in ['tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv',
          'campaign/results/sleeve_library/XGB1y_deploy.csv']:
    st = os.stat(f'{R}/{p}')
    print(p, "mtime", datetime.datetime.fromtimestamp(st.st_mtime), "size", st.st_size)
