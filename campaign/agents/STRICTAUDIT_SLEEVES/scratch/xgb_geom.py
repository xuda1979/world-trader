import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
n_days = x.groupby(per).size()
# geometric spread: v = (1+ls_net)^(1/N)-1
v = (1+m2.reindex(n_days.index))**(1/n_days) - 1
mapped = np.asarray(per.map(v), dtype=float)
xs = x[mapped==mapped]
vv = pd.Series(mapped[mapped==mapped], index=xs.index)
d = np.abs(xs.values - vv.values)
print(f"GEOMETRIC spread: max|d|={d.max():.3e} exact(<=1e-15)={(d<=1e-15).sum()} <=1e-12:{(d<=1e-12).sum()} n={len(xs)}")
print(f"rows before monthly start (lead-in zeros): {len(x)-len(xs)}")
