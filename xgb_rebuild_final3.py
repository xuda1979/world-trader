import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
mapped = per.map(m2).astype(float)          # np array w/ NaN where absent
xs = x[mapped==mapped]                       # keep non-NaN
mv = pd.Series(mapped[mapped==mapped], index=xs.index)
n_days = x.groupby(per).size()
nd = pd.Series(n_days.reindex(xs.index.to_period('M')).astype(float).values, index=xs.index)
spread = mv/nd
print(f"cum file={xs.sum():.6f} cum spread={spread.sum():.6f} ratio={spread.sum()/xs.sum():.4f}")
print(f"corr daily = {np.corrcoef(xs.values, spread.values)[0,1]:.6f}")
SLEEVES = ['../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv','../../../agents/COORD/sleeves/brwt10_2000.csv','../../../agents/COORD/sleeves/brwt7.csv','../../../agents/COORD/sleeves/brwt5.csv','../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv','../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv','../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv','../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv','../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv','../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv','../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv']
alld = pd.concat([pd.read_csv(p, parse_dates=['date'])['date'] for p in SLEEVES]).drop_duplicates().sort_values()
alldp = pd.Series(1.0, index=alld).groupby(alld.to_period('M')).sum()
bn = pd.Series(alldp.reindex(xs.index.to_period('M')).astype(float).values, index=xs.index)
spread2 = mv/bn
d = np.abs(xs.values - spread2.values)
print(f"union-N spread: max|d|={d.max():.3e} exact={(d<=1e-12).sum()}/{len(xs)} cumratio={spread2.sum()/xs.sum():.4f} corr={np.corrcoef(xs.values,spread2.values)[0,1]:.6f}")
