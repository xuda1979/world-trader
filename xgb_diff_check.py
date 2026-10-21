import pandas as pd, numpy as np, subprocess
R='/Users/daxu/software/world-trader'
# committed version of monthly file (4662a6a) vs working copy
blob = subprocess.run(['git','-C',R,'show','4662a6a:tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
print("git show exit:", blob.returncode, "lines:", len(blob.stdout.splitlines()))
import io
s_c = pd.read_csv(io.StringIO(blob.stdout), index_col=0, parse_dates=True).iloc[:,0]
s_w = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv', index_col=0, parse_dates=True).iloc[:,0]
print(f"committed rows={len(s_c)} working rows={len(s_w)}")
j = pd.concat([s_c.rename('committed'), s_w.rename('working')],axis=1)
common = j.dropna()
print(f"common={len(common)} max|diff|={(common['committed']-common['working']).abs().max():.3e} identical={np.allclose(common['committed'],common['working'])}")
# is working file modified vs git?
st = subprocess.run(['git','-C',R,'status','--porcelain','tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
print("git status:", repr(st.stdout))
# now rebuild with COMMITTED source
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
per = x.index.to_period('M')
m2 = pd.Series(s_c.values, index=pd.PeriodIndex(s_c.index, freq='M'))
built = pd.Series(per.map(m2).astype(float).values, index=x.index)
ok = built.notna()
diff = (x[ok]-built[ok]).abs()
print(f"committed-source rebuild: n={ok.sum()} max|d|={diff.max():.3e} exact={(diff<=1e-12).sum()}")
# 2nd source candidate: gkx_1y_blend_monthly.csv
s_b = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_blend_monthly.csv', index_col=0, parse_dates=True).iloc[:,0]
m2b = pd.Series(s_b.values, index=pd.PeriodIndex(s_b.index, freq='M'))
builtb = pd.Series(per.map(m2b).astype(float).values, index=x.index)
okb = builtb.notna()
diffb = (x[okb]-builtb[okb]).abs()
print(f"blend-monthly rebuild: n={okb.sum()} max|d|={diffb.max():.3e} exact={(diffb.abs()<=1e-12).sum()} corr={x[okb].corr(builtb[okb]):.4f}")
