import pandas as pd, numpy as np, os
# Attempt exact rebuild of XGB1y_deploy.csv from gkx_1y_deploy_monthly.csv (committed?)
R='/Users/daxu/software/world-trader'
P1=f'{R}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv'
print("monthly in git:", os.system(f"git -C {R} ls-files --error-unmatch tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv >/dev/null 2>&1 && echo YES || echo NO"))
os.system(f"git -C {R} ls-files --error-unmatch tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv 2>/dev/null && echo TRACKED || echo UNTRACKED")
m = pd.read_csv(P1, parse_dates=[0]).set_index(m.columns[0] if False else pd.read_csv(P1).columns[0])
m = pd.read_csv(P1, index_col=0, parse_dates=True)
s = m.iloc[:,0]
x = pd.read_csv(f'{R}/campaign/results/sleeve_library/XGB1y_deploy.csv', parse_dates=['date']).set_index('date')['ret']
x = pd.to_numeric(x, errors='coerce').dropna()
# spread each monthly value across its month's trading days in XGB1y calendar
xp = x.copy()
xp.index = xp.index.to_period('M')
m2 = s.copy(); m2.index = pd.PeriodIndex(m2.index, freq='M')
built = xp.index.map(m2)
diff = (x.values - built.values)
print(f"n={len(x)} months={x.index.nunique()} max|diff|={np.nanmax(np.abs(diff)):.3e} corr={np.corrcoef(x.values, built.values)[0,1]:.8f}")
print(f"exact rows (diff<1e-12): {(np.abs(diff)<1e-12).sum()}")
# zero rows in x vs monthly value
zero_rows = x.abs()<1e-12
print(f"zero rows: {zero_rows.sum()}, monthly value there: {m2.reindex(xp.index[zero_rows]).dropna().abs().sum()}")
# does the daily file begin 2008-01 (before monthly starts 2009-02)? => lead-in zeros
print("daily file start:", x.index[0].date(), "monthly start:", s.index[0].date())
