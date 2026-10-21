import pandas as pd, numpy as np
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv', parse_dates=['date']).set_index('date')
r = pd.to_numeric(ch['ret'], errors='coerce').dropna()
print(f"arith ann = mean*252 = {r.mean()*252*100:.1f}%")
print(f"geo ann 252 = {((1+r).prod()**(252/len(r))-1)*100:.1f}%")
print(f"vol_d={r.std()*100:.3f}% vol_ann={r.std()*np.sqrt(252)*100:.1f}%")
print(f"SR_d*vol_ann = {r.mean()/r.std()*np.sqrt(252)*r.std()*np.sqrt(252)*100:.1f}%")
oos = r[r.index>='2017-01-01']
print(f"OOS arith = {oos.mean()*252*100:.1f}%; geo = {((1+oos).prod()**(252/len(oos))-1)*100:.1f}%")
# what happens 2020-09-01 across sleeves
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
print("\n2020-09-01 sleeve returns:")
for k,p in SLEEVES.items():
    s = pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce')
    if '2020-09-01' in s.index:
        print(f"  {k:9s} {s.loc['2020-09-01']*100:+.2f}%")
print(f"champion 2020-09-01: {r.loc['2020-09-01']*100:+.2f}%")
# top 5 champion days
print("\ntop5 |champion| days:")
print((r.abs().sort_values(ascending=False).head(5)*100).round(2))
print((r.loc[r.abs().sort_values(ascending=False).head(5).index]*100).round(2))
