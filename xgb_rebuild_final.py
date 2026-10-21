import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
# Daily file starts 2008-01; monthly starts 2009-02. ratio>file_days => N was computed on a LARGER grid (union panel incl holidays?)
# The union panel likely has ~252-ish days/yr with some months 23-24. ratio avg 21.1 vs file 21.1-ish but offset ±1.
# Test: N(m) = number of UNION PANEL dates in month m. Reconstruct proxy: count of DATES in any of the 12 sleeve files?
# Simpler test: does sum over month m of file equal m2/ something stable? compute total cum.
# What matters for the champion: aggregate level. Compare cumulative sums.
ok = per.map(m2).notna()
xs = x[ok]; bs = per[ok].map(m2)
print(f"cum sum file = {xs.sum():.6f}; cum sum spread(monthly value each day / file_days) =")
n_days = x.groupby(per).size()
spread = per[ok].map(m2)/per[ok].map(n_days).astype(float)
print(f"{spread.sum():.6f}  (ratio {spread.sum()/xs.sum():.6f})")
print(f"corr file-vs-spread daily = {np.corrcoef(xs.values, spread.values)[0,1]:.6f}")
# Try N = union panel trading days: count distinct dates across all 12 sleeve CSVs per month
SLEEVES = ['../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv','../../../agents/COORD/sleeves/brwt10_2000.csv','../../../agents/COORD/sleeves/brwt7.csv','../../../agents/COORD/sleeves/brwt5.csv','../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv','../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv','../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv','../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv','../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv','../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv','../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv']
alld = pd.concat([pd.read_csv(p, parse_dates=['date'])['date'] for p in SLEEVES]).drop_duplicates().sort_values()
alldp = pd.Series(1, index=alld).groupby(alld.to_period('M')).sum()
builtN = per[ok].map(alldp).astype(float)
spread2 = per[ok].map(m2)/builtN
d = (xs.values - spread2.values)
print(f"union-panel-N spread: max|d|={np.abs(d).max():.3e} exact={(np.abs(d)<=1e-12).sum()}/{ok.sum()} cumratio={spread2.sum()/xs.sum():.6f}")
