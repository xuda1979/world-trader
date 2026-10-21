import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
def gitshow(rev, path):
    r = subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,text=True)
    return pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]

x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
s = gitshow('4662a6a','software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv')
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
n_days = x.groupby(per).size()
# implied N per month from data: N = monthly_src / daily_value
dvals = x.groupby(per).first()
with np.errstate(all='ignore'):
    N_impl = m2.reindex(dvals.index) / dvals
print(N_impl.describe())
print("unique-ish:", N_impl.round(2).head(24).to_dict())
# 22 vs implied 22.83? calendar days?
# check calendar-day counts
import calendar
def caldays(p):
    return pd.Period(p,'M').end_time.day
N_cal = pd.Series([caldays(p) for p in n_days.index], index=n_days.index)
built = pd.Series(per.map(m2.reindex(n_days.index)/N_cal).astype(float).values, index=x.index)
ok = built.notna()
d=(x[ok]-built[ok]).abs()
print(f"calendar-day spread: max|d|={d.max():.3e} exact={(d<=1e-12).sum()}/{ok.sum()}")
