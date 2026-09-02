import pandas as pd, numpy as np
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
ROOT="/Users/daxu/software/world-trader"
r=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
idx=r.index
# 1. weekends?
wknd=idx[idx.dayofweek>=5]
print("weekend dates in CSV:",len(wknd))
# 2. US federal holidays present?
cal=USFederalHolidayCalendar(); fed=set(cal.holidays(start='2006-01-01',end='2026-12-31').date)
fed_in=idx[[d.date() in fed for d in idx]]
print("US-federal-holiday dates in CSV:",len(fed_in), [str(d.date()) for d in fed_in[:5]])
# 3. Good Friday (NYSE closed, federal open): NYSE rule = Good Friday
# compute Easter via dateutil.easter
from dateutil.easter import easter
gf=set()
for y in range(2008,2027):
    e=easter(y)
    gf.add(pd.Timestamp(e)-pd.Timedelta(days=2))
gf_in=idx[[pd.Timestamp(d) in gf for d in idx]]
print("Good Friday dates in CSV:",len(gf_in), [str(d.date()) for d in gf_in])
# 4. compare CSV calendar vs NYSE-ish calendar: all Mon-Fri non-federal days 2008-2026 missing?
allbd=pd.bdate_range('2008-03-31','2026-07-31')
missing=set(allbd)-set(idx)
miss_fed=[d for d in missing if d.date() in fed]
miss_gf=[d for d in missing if pd.Timestamp(d) in gf]
miss_other=[d for d in missing if d.date() not in fed and d.date() not in gf]
print(f"total bdays 2008-03-31..2026-07-31: {len(allbd)}, in csv {len(idx)}, missing {len(missing)}")
print(f"  missing & federal holiday: {len(miss_fed)} e.g.", [str(d.date()) for d in sorted(miss_fed)[:8]])
print(f"  missing & Good Friday: {len(miss_gf)}")
print(f"  missing & other (unexplained): {len(miss_other)}", [str(d.date()) for d in sorted(miss_other)[:15]])
# 5. Columbus Day / Veterans Day (federal but NYSE OPEN) - do sleeves have data those days?
print("\nColumus/Veterans days in CSV:",sum(1 for d in idx if (d.month==10 and d.dayofweek==0 and 8<=d.day<=14) or (d.month==11 and d.dayofweek==2 and 8<=d.day<=14)))
# sleeve-level: check one sleeve for Good Friday rows
s=pd.read_csv(f"{ROOT}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",index_col=0,parse_dates=True).iloc[:,0]
sgf=s.index[[pd.Timestamp(d) in gf for d in s.index]]
print("sleeve brwt15 rows on Good Friday (raw file):",len(sgf))
