import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
n_days = x.groupby(per).size()
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
# geometric: v = (1+ls)^(1/N)-1
v = (1+m2.reindex(n_days.index))**(1/n_days)-1
mapped = np.asarray(per.map(v), dtype=float)
xs = x[mapped==mapped]
vv = pd.Series(mapped[mapped==mapped], index=xs.index)
d = np.abs(xs.values-vv.values)
# verify whole file: total cum growth comparison
tot_file = (1+x).prod()-1
tot_src_geometric = (1+v.reindex(n_days.index).dropna()).prod()-1
print(f"GEOMETRIC exact rows: {(d<=1e-15).sum()}/{len(xs)} max|d|={d.max():.2e}")
print(f"cum file={tot_file:.8f}; monthly source compounded={((1+s.dropna()).prod()-1):.8f}")
# XGB1y SR monthly on valid months:
mr=(1+x).groupby(per).prod()-1
mv=mr[mr.index>=pd.Period('2009-02','M')]
print(f"XGB1y monthly SR 2009-02+: {mv.mean()/mv.std()*np.sqrt(12):.3f} (meta claims 1.06)")
