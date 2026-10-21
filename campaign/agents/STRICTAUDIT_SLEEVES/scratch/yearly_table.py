import pandas as pd, numpy as np
# Final per-sleeve yearly tables for verdict (2008+ window as in champion)
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
rows=[]
for k,p in SLEEVES.items():
    r = pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce').dropna()
    r08 = r[r.index>='2008-09-01']
    sr = r08.mean()/r08.std()*np.sqrt(252)
    sr_full = r.mean()/r.std()*np.sqrt(252)
    yr=(1+r08).groupby(r08.index.year).prod()-1
    rows.append((k, round(sr_full,2), round(sr,2), round(float((yr<0).sum()),0), len(yr), round(float(yr.min())*100,1), round(float(yr.max())*100,1)))
print(f"{'sleeve':9s} SRfull SR08+ negyrs/ny worst% best%")
for r_ in rows: print(f"{r_[0]:9s} {r_[1]:>6} {r_[2]:>5} {int(r_[3]):>3}/{r_[4]:<3} {r_[5]:>6} {r_[6]:>6}")
