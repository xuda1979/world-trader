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
built = pd.Series(per.map(m2).astype(float).values, index=x.index)
ok = built.notna()
# Hypothesis: daily value = pnl(m)/N_business_days(m) where N = TRADING days in month per NYSE-ish calendar of the DAILY FILE
n_days = x.groupby(per).size()
spread_alt = m2.reindex(n_days.index) / n_days
built2 = pd.Series(per.map(spread_alt).astype(float).values, index=x.index)
ok2 = built2.notna()
d2 = (x[ok2]-built2[ok2]).abs()
print(f"spread=monthly/N(days in file): max|d|={d2.max():.3e} exact={(d2<=1e-12).sum()}/{ok2.sum()}")
# Hypothesis: N from source month (end-start)
# Check a single month in detail
mm = pd.Period('2023-05','M')
sel = (per==mm)
print("\n2023-05: source ls_net:", m2.get(mm), "n_days:", n_days.get(mm), "spread:", spread_alt.get(mm))
print("file values that month:", x[sel].describe().to_dict())
print("first/last:", x[sel].index[0].date(), x[sel].index[-1].date())
print("sum file month:", x[sel].sum(), " vs src:", m2.get(mm))
