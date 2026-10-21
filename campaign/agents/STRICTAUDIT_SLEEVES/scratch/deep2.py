import pandas as pd, numpy as np

SLEEVES = {
 'C5ng':   '../../../agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv',
 'A5r2':   '../../../agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv',
 'a6r7':   '../../../agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv',
 'C5ngsum':'../../../agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv',
 'dualmom':'../../../agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv',
 'XGB1y':  '../../../results/sleeve_library/XGB1y_deploy.csv',
}
R = {}
for name, path in SLEEVES.items():
    df = pd.read_csv(path, parse_dates=['date']).set_index('date')
    R[name] = pd.to_numeric(df['ret'], errors='coerce')

x = R['XGB1y'].dropna()
mr = (1+x).groupby(x.index.to_period('M')).prod()-1
yr = (1+mr).groupby(mr.index.year).prod()-1
print(f"XGB1y neg years: {(yr<0).sum()}/{len(yr)}; worst {yr.min()*100:.1f}% ({yr.idxmin()}); yearly:")
print((yr*100).round(1))

# Zero-run extraction (interior only), exact dates
def runs_ge(r, minlen):
    z = (r.abs() < 1e-12)
    grp = (z != z.shift()).cumsum()
    out = []
    for k, g in z.groupby(grp):
        if bool(g.iloc[0]) and len(g) >= minlen:
            out.append((str(g.index[0].date()), str(g.index[-1].date()), len(g)))
    return out

for k, ml in [('a6r7',200),('dualmom',100),('A5r2',90),('C5ngsum',100)]:
    r = R[k].dropna()
    nz = np.where(r.abs()>=1e-12)[0]
    interior = r.iloc[nz[0]:nz[-1]+1]
    print(f"\n{k} interior runs >= {ml}d:")
    for run in runs_ge(interior, ml):
        print("  ", run)
