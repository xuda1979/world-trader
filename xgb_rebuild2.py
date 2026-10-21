import pandas as pd, numpy as np
R='/Users/daxu/software/world-trader'
m = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv', index_col=0, parse_dates=True)
s = m.iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
# rebuild: for each daily date, take monthly value of that date's month (pandas period)
per = x.index.to_period('M')
# build mapping from period -> value (use month END date in source; period from it)
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
built = per.map(m2).astype(float)
ok = built.notna()
diff = (x[ok] - built[ok])
print(f"rows with month in source: {ok.sum()}/{len(x)}; max|diff|={diff.abs().max():.3e}; exact(<=1e-12): {(diff.abs()<=1e-12).sum()}")
print(f"corr = {x[ok].corr(built[ok]):.10f}")
print("rows before monthly start (lead-in):", (~ok).sum())
# check convention: value stamped on month containing the month-END stamp
# alt convention: value stamped on NEXT month (label lag)
m3 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M').shift(1) if False else pd.PeriodIndex(s.index, freq='M'))
built_next = per.map(pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M')+1)).astype(float)
diff_next = (x[ok] - built_next[ok])
print(f"alt-convention (value in month m+1): max|diff|={np.nanmax(np.abs(diff_next)):.3e} exact={(diff_next.abs()<=1e-12).sum()}")
