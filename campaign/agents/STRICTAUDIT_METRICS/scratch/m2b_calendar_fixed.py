# m2b: corrected NYSE calendar; full missing-day forensics; SPY check on missing days
import pandas as pd, numpy as np, datetime as dt, glob, os

CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:,0].sort_index()

def easter(year):
    a=year%19; b=year//100; c=year%100; d_=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d_-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
    return dt.date(year,month,day)

def nth_weekday(year, month, weekday, n):  # weekday: 0=Mon..4=Fri
    d = dt.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + dt.timedelta(days=offset + 7*(n-1))

def last_weekday(year, month, weekday):
    d = dt.date(year, month+1, 1) - dt.timedelta(days=1) if month<12 else dt.date(year,12,31)
    return d - dt.timedelta(days=(d.weekday()-weekday)%7)

def obs(d0):
    if d0.weekday()==5: return d0-dt.timedelta(days=1)
    if d0.weekday()==6: return d0+dt.timedelta(days=1)
    return d0

def nyse_holidays(year):
    H=set()
    H.add(obs(dt.date(year,1,1)))
    H.add(nth_weekday(year,1,0,3))            # MLK
    H.add(nth_weekday(year,2,0,3))            # Washington
    H.add(easter(year)-dt.timedelta(days=2))  # Good Friday
    H.add(last_weekday(year,5,0))             # Memorial
    if year>=2022: H.add(obs(dt.date(year,6,19)))
    H.add(obs(dt.date(year,7,4)))
    H.add(nth_weekday(year,9,0,1))            # Labor
    H.add(nth_weekday(year,11,3,4))           # Thanksgiving 4th Thursday
    H.add(obs(dt.date(year,12,25)))
    if year==2012: H|= {dt.date(2012,10,29), dt.date(2012,10,30)}   # Sandy
    if year==2011: H.add(dt.date(2011,8,29))                        # Irene
    if year==2018: H.add(dt.date(2018,12,5))                        # Bush 41 mourning
    if year==2025: H.add(dt.date(2025,1,9))                         # Carter mourning
    return H

start, end = r.index[0].date(), r.index[-1].date()
closed=set()
for y in range(start.year, end.year+1):
    for h in nyse_holidays(y): closed.add(pd.Timestamp(h))
allDays = pd.date_range(start, end, freq="D")
nyse = pd.DatetimeIndex([d for d in allDays if d.weekday()<5 and d not in closed])
print(f"corrected NYSE open days {start}..{end}: {len(nyse)}  (rows/yr = {len(nyse)/((end-start).days/365.25):.1f})")
in_csv=set(r.index)
bad = [d for d in r.index if d not in set(nyse)]
print(f"CSV dates not NYSE-open: {len(bad)}", [(str(d.date())) for d in bad[:20]])
missing = pd.DatetimeIndex([d for d in nyse if d not in in_csv])
print(f"NYSE-open days MISSING from CSV: {len(missing)}")
print("\nper-year missing counts:")
mc = pd.Series(1, index=missing).groupby(missing.year).sum()
print(mc.to_string())

# weekday/month profile of missing days
print("\nweekday profile:", missing.day_name().value_counts().to_dict())
print("month profile:", missing.month.value_counts().sort_index().to_dict())
print("\nfull missing list:")
for d in missing: print("  ", d.date(), d.day_name())

# ---- SPY ground truth on missing days ----
cands = glob.glob("/Users/daxu/software/world-trader/**/SPY*.csv", recursive=True) + \
        glob.glob("/Users/daxu/software/world-trader/**/*spy*.csv", recursive=True) + \
        glob.glob("/Users/daxu/software/world-trader/**/SPY*.parquet", recursive=True)
print("\nSPY file candidates:", cands[:10])
