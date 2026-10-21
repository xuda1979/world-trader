import pandas as pd, numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar
from dateutil.easter import easter
ROOT="/Users/daxu/software/world-trader"
r=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
idx=set(r.index)
cal=USFederalHolidayCalendar(); fed=set(cal.holidays(start='2006-01-01',end='2026-12-31'))
gf=set(pd.Timestamp(easter(y))-pd.Timedelta(days=2) for y in range(2008,2027))
allbd=pd.bdate_range('2008-03-31','2026-07-31')
missing=[d for d in allbd if d not in idx]
oth=[d for d in missing if d not in fed and d not in gf]
print(f"unexplained missing {len(oth)}: motive guess per date (check against sleeve raw coverage)")
# count how many of the 11 sleeves have a row on each unexplained date
import glob
files={
 "brwt15":"campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 "brwt10":"campaign/agents/COORD/sleeves/brwt10_2000.csv",
 "brwt7":"campaign/agents/COORD/sleeves/brwt7.csv",
 "brwt5":"campaign/agents/COORD/sleeves/brwt5.csv",
 "C5ng":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2":"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 "a6r7":"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv"}
cov={}
for n,p in files.items():
    s=pd.read_csv(f"{ROOT}/{p}",index_col=0,parse_dates=True).iloc[:,0]
    cov[n]=set(s.index)
rows=[]
for d in sorted(oth):
    have=sum(1 for n in cov if d in cov[n])
    rows.append((d.strftime('%Y-%m-%d %a'),have))
for x in rows: print(x)
import collections
print(collections.Counter(h for _,h in rows))
