import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s_c = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
s_w = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv', index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([s_c.rename('committed'), s_w.rename('working')],axis=1).dropna()
d=(j['committed']-j['working']).abs()
print(f"monthly file: committed rows={len(s_c)} working rows={len(s_w)} common={len(j)}")
print(f"diff months: {(d>1e-12).sum()} max|d|={d.max():.4f}")
print("first differing months:")
print(j[d>1e-12].head(5))
# and does champion input (XGB1y_deploy.csv) match committed or working?
x = pd.to_numeric(pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv',parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
per = x.index.to_period('M')
n_days = x.groupby(per).size()
for nm, s in [('committed',s_c),('working',s_w)]:
    v=(1+pd.Series(s.values,index=pd.PeriodIndex(s.index,freq='M')).reindex(n_days.index))**(1/n_days)-1
    mapped=np.asarray(per.map(v),dtype=float)
    xs=x[mapped==mapped]; vv=pd.Series(mapped[mapped==mapped],index=xs.index)
    dd=np.abs(xs.values-vv.values)
    print(f"XGB1y_deploy.csv matches {nm} monthly: exact {(dd<=1e-15).sum()}/{len(xs)} max|d|={dd.max():.2e}")
