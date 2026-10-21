import pandas as pd, numpy as np

# Champion stats
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv', parse_dates=['date']).set_index('date')
r = pd.to_numeric(ch['ret'], errors='coerce').dropna()
sr = r.mean()/r.std()*np.sqrt(252)
ann = (1+r).prod()**(252/len(r))-1
cum = (1+r).cumprod(); mdd = (cum/cum.cummax()-1).min()
yr = (1+r).groupby(r.index.year).prod()-1
oos = r[r.index>='2017-01-01']
sroos = oos.mean()/oos.std()*np.sqrt(252)
print(f"CHAMPION STRICTTRADE: n={len(r)} span {r.index[0].date()}..{r.index[-1].date()}")
print(f"ann={ann*100:.1f}% SR_d={sr:.2f} MaxDD={mdd*100:.1f}% negyrs={(yr<0).sum()}/{len(yr)} worst_yr={yr.min()*100:.1f}%({yr.idxmin()}) best={yr.max()*100:.1f}%({yr.idxmax()}) OOS(2017+) SR={sroos:.2f} ann={((1+oos).prod()**(252/len(oos))-1)*100:.1f}%")
# claimed: ann 49.4 SR 5.24 mdd -6.1, 0/19 neg, worst +20.7 (2026 partial), best 151.1 2023, OOS 55.9
# monthly SR
mr = (1+r).groupby(r.index.to_period('M')).prod()-1
print(f"SR_monthly={mr.mean()/mr.std()*np.sqrt(12):.2f} (claimed 3.46)")

# weekend rows in champion
wd = r.index.dayofweek
print(f"champion weekend rows: sat={int((wd==5).sum())} sun={int((wd==6).sum())}")

# max daily
i = r.abs().idxmax()
print(f"champion max|ret| = {abs(r.loc[i])*100:.2f}% on {i.date()}")

# correlation of each sleeve to champion (overlap)
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
print("\nsleeve corr to champion (raw, overlap):")
for k, p in SLEEVES.items():
    s = pd.to_numeric(pd.read_csv(p, parse_dates=['date']).set_index('date')['ret'], errors='coerce')
    j = pd.concat([s.rename('a'), r.rename('c')], axis=1, sort=True).dropna()
    print(f"  {k:9s} n={len(j):5d} corr={j['a'].corr(j['c']):+.3f}")
