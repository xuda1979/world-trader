import pandas as pd, numpy as np
# T+1 check on champion level: corr of champion ret(t) with sleeve mean ret(t+1)? 
# Simpler: verify no champion return on days when ALL sleeves are zero/NaN, and vice versa.
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
P = {k: pd.to_numeric(pd.read_csv(p,parse_dates=['date']).set_index('date')['ret'],errors='coerce') for k,p in SLEEVES.items()}
ch = pd.read_csv('../../../results/GOAL100_STRICTTRADE_BALANCED_daily.csv',parse_dates=['date']).set_index('date')
rc = pd.to_numeric(ch['ret'],errors='coerce').dropna()
# sleeve index coverage of champion dates
missing = [d for d in rc.index if sum((d in P[k].dropna().index) for k in P)==0]
print("champion days with NO sleeve data:", len(missing), missing[:5])
# partial coverage days (e.g., early champion before A5r2 start)
cov = pd.Series([sum((d in P[k].dropna().index) for k in P) for d in rc.index], index=rc.index)
print("coverage distribution:", cov.value_counts().sort_index().to_dict())
# is champion NaN-row count = 0 on 2008-03-31..2008-09 (pre A5r2)? then uses brwt+natgas+a6r7+QAxasts+carryv2+dualmom+XGB
