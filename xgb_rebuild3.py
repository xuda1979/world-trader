import pandas as pd, numpy as np
R='/Users/daxu/software/world-trader'
m = pd.read_csv(f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv', index_col=0, parse_dates=True)
s = m.iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
per = x.index.to_period('M')
m2 = pd.Series(s.values, index=pd.PeriodIndex(s.index, freq='M'))
built = pd.Series(per.map(m2).astype(float).values, index=x.index)
ok = built.notna()
diff = (x[ok] - built[ok])
print(f"n_ok={ok.sum()}/{len(x)} max|diff|={diff.abs().max():.3e} exact={(diff.abs()<=1e-12).sum()} corr={x[ok].astype(float).corr(built[ok]):.10f}")
# month-level check: aggregate x monthly and compare to source
mr = (1+x).groupby(x.index.to_period('M')).prod()-1
j = pd.concat([mr.rename('daily_agg'), m2.rename('monthly_src')], axis=1).dropna()
j['diff'] = (j['daily_agg']-j['monthly_src']).abs()
print("monthly agg vs source: n=", len(j), "max|diff|=", j['diff'].max())
print(j[j['diff']>1e-10].head(10))
