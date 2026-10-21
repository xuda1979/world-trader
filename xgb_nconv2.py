import pandas as pd, numpy as np, subprocess, io
R='/Users/daxu/software/world-trader'
r = subprocess.run(['git','-C',R,'show','4662a6a:software/world-trader/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'],capture_output=True,text=True)
s = pd.read_csv(io.StringIO(r.stdout), index_col=0, parse_dates=True).iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
dvals = x.groupby(per).first()
# implied N looks like union-panel trading days per month (incl holidays) ~ pd date_range B?
idx = pd.bdate_range('2009-01-01','2026-08-31')
nb = pd.Series(1, index=idx).groupby(idx.to_period('M')).sum()
print("bdate-month counts 2009:", nb.head(6).to_dict())
ratio = m2.reindex(dvals.index)/dvals
print("ratio vs bdate count:", (ratio - nb.reindex(ratio.index)).abs().max())
# maybe N = month-end to month-end calendar days /? try N = days between month start and next month start (cal)
alt = pd.Series([pd.Period(p+1,'M').start_time - pd.Period(p,'M').start_time for p in dvals.index], index=dvals.index).dt.days
print("ratio vs 30/31:", (ratio - alt).abs().describe().to_dict())
# Actually try: pnl(m)/N where N = number of rows for month m in the file INCLUDING any extra? n_days we had 22 for 2023-05, ratio 22.83
print("2023-05 ratio:", (m2[pd.Period('2023-05','M')]/dvals[pd.Period('2023-05','M')]))
# try N = union-panel business days (Mon-Fri minus nothing)
udays = pd.date_range('2009-01-01','2026-08-31',freq='D')
# weekdaily excluding weekends only = bdate. Try: month m days = date_range in union panel month grid
# print a few months' (src/val) and n_days(file)
cmp = pd.DataFrame({'ratio':ratio, 'file_days':x.groupby(per).size()})
print(cmp.head(30))
