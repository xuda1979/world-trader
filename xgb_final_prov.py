import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
def gitshow(rev, path):
    r = subprocess.run(['git','-C',R,'show',f'{rev}:{path}'],capture_output=True,text=True)
    if r.returncode != 0: return None
    return pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]

x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')

cands = {
 'gkx_1y_deploy_monthly@HEAD': ('HEAD','tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'),
 'gkx_1y_blend_monthly@HEAD': ('HEAD','tools/quant/reports/xgb_horizons/gkx_1y_blend_monthly.csv'),
 'daily_1y_monthly@HEAD': ('HEAD','tools/quant/reports/xgb_horizons/daily_1y_monthly.csv'),
}
for name,(rev,path) in cands.items():
    s = gitshow(rev,path)
    if s is None: print(name, "NOT IN GIT at", rev); continue
    # normalize: some files may have col name 'ls_net'; value scale may be % -> check
    best = None
    for shift in range(-2,3):
        m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M')+shift)
        built = pd.Series(per.map(m2).astype(float).values, index=x.index)
        ok = built.notna()
        if ok.sum()<100: continue
        d = (x[ok]-built[ok]).abs()
        if best is None or d.max() < best[1]: best = (shift, d.max(), (d<=1e-12).sum(), ok.sum())
    if best: print(f"{name}: best shift {best[0]:+d} n={best[3]} max|d|={best[1]:.3e} exact={best[2]}")
