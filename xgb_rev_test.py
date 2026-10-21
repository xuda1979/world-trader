import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
def gitshow(rev, path):
    r = subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,text=True)
    if r.returncode != 0: return None
    return pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]

x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
P='software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'
for rev in ['4662a6a','335eff0','HEAD']:
    s = gitshow(rev, P)
    if s is None: print(rev, "absent"); continue
    m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
    built = pd.Series(per.map(m2).astype(float).values, index=x.index)
    ok = built.notna()
    d=(x[ok]-built[ok]).abs()
    # month-level compare
    mr = (1+x).groupby(x.index.to_period('M')).prod()-1
    jj = pd.concat([mr.rename('agg'), m2.rename('src')],axis=1).dropna()
    dd=(jj['agg']-jj['src']).abs()
    print(f"rev {rev}: rows={len(s)} n_ok={ok.sum()} daily max|d|={d.max():.3e} exact={(d<=1e-12).sum()} | month-level: n={len(jj)} max|d|={dd.max():.3e} exact={(dd<=1e-12).sum()}")
