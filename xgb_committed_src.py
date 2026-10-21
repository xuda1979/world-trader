import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
def gitshow(rev, path):
    r = subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,text=True)
    if r.returncode != 0: return None
    return pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]

x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
paths = ['tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv',
         'tools/quant/reports/xgb_horizons/daily_1y_monthly.csv']
for p in paths:
    s_c = gitshow('HEAD', p)   # path relative to repo root: include software/world-trader prefix
    if s_c is None:
        s_c = gitshow('HEAD', 'software/'+p)
    if s_c is None: print(p, "unavailable at HEAD"); continue
    best=None
    for shift in range(-2,3):
        m2 = pd.Series(s_c.values, index=pd.PeriodIndex(s_c.index, freq='M')+shift)
        built = pd.Series(per.map(m2).astype(float).values, index=x.index)
        ok = built.notna()
        if ok.sum()<100: continue
        d=(x[ok]-built[ok]).abs()
        if best is None or d.max()<best[1]: best=(shift,d.max(),(d<=1e-12).sum(),ok.sum())
    print(f"{p}: best shift {best[0]:+d} n={best[3]} max|d|={best[1]:.3e} exact={best[2]}")
