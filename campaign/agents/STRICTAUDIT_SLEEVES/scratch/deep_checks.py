import pandas as pd, numpy as np

SLEEVES = {
 'brwt15': '../../../agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv',
 'brwt10': '../../../agents/COORD/sleeves/brwt10_2000.csv',
 'brwt7':  '../../../agents/COORD/sleeves/brwt7.csv',
 'brwt5':  '../../../agents/COORD/sleeves/brwt5.csv',
 'C5ng':   '../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
 'C5ngsum':'../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
 'A5r2':   '../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',
 'a6r7':   '../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',
 'QAxasts':'../../../agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv',
 'carryv2':'../../../agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv',
 'dualmom':'../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',
 'XGB1y':  '../../../results/sleeve_library/XGB1y_deploy.csv',
}
R = {}
for name, path in SLEEVES.items():
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    R[name] = pd.to_numeric(df['ret'], errors='coerce')

# 1. weekend rows per sleeve
print("=== weekend-day rows (Sat/Sun) ===")
for k, r in R.items():
    wd = r.dropna().index.dayofweek
    print(f"{k:9s} sat={int((wd==5).sum())} sun={int((wd==6).sum())}")

# 2. C5ng max |ret| date
r = R['C5ng'].dropna()
i = r.abs().idxmax()
print(f"\nC5ng max|ret| {r.loc[i]*100:.2f}% on {i.date()}; top5:")
print((r.abs().sort_values(ascending=False).head(5)*100).round(2))

# 3. carryv2 max |ret|
r = R['carryv2'].dropna(); i = r.abs().idxmax()
print(f"\ncarryv2 max|ret| {r.loc[i]*100:.2f}% on {i.date()}")
r = R['QAxasts'].dropna(); i = r.abs().idxmax()
print(f"QAxasts max|ret| {r.loc[i]*100:.2f}% on {i.date()}")

# 4. XGB1y monthly-constant check
x = R['XGB1y'].dropna()
g = x.groupby(x.index.to_period('M'))
nunique = g.nunique()
print(f"\nXGB1y: {len(x)} rows, {x.index.to_period('M').nunique()} months; months with >1 distinct value: {(nunique>1).sum()}")
print("std within month: max =", g.std().max())
# monthly aggregation
mr = (1+x).groupby(x.index.to_period('M')).prod()-1
sr_m = mr.mean()/mr.std()*np.sqrt(12)
print(f"XGB1y monthly-compounded SR (ann): {sr_m:.3f}; monthly mean {mr.mean()*100:.2f}% std {mr.std()*100:.2f}%")
yr = (1+mr).groupby(x.index.year).prod()-1
print(f"XGB1y neg years: {(yr<0).sum()}/{len(yr)}; worst {yr.min()*100:.1f}% ({yr.idxmin()})")

# 5. zero-run date extraction for flagged sleeves
def longest_run_dates(r, minlen=90):
    z = (r.abs() < 1e-12)
    z = z.reindex(pd.date_range(r.index[0], r.index[-1], freq='D'), fill_value=False)
    z = z[z.index.isin(r.index)]
    runs = []
    grp = (z != z.shift()).cumsum()
    for k, g_ in z.groupby(grp):
        if g_.all() and len(g_) >= minlen:
            runs.append((str(g_.index[0].date()), str(g_.index[-1].date()), len(g_)))
    return runs
for k in ['a6r7', 'dualmom', 'A5r2', 'C5ngsum']:
    print(f"\n{k} zero-runs >=90d:", longest_run_dates(R[k].dropna(), 90))
