# STRICTAUDIT_METRICS m2: internal consistency + NYSE calendar forensics
import pandas as pd, numpy as np, datetime as dt

CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:,0].sort_index()

print("== basics ==")
print("strictly increasing:", r.index.is_monotonic_increasing and (np.diff(r.index.values).astype('timedelta64[D]').astype(int) > 0).all())
print("duplicate dates:", int(r.index.duplicated().sum()))
print("NaN:", int(r.isna().sum()), " inf:", int(np.isinf(r.values).sum()))
print("max single-day |ret|: %.4f%% on %s" % (r.abs().max()*100, r.abs().idxmax().date()))
print("min daily: %.4f%% (%s)  max daily: %.4f%% (%s)" % (r.min()*100, r.idxmin().date(), r.max()*100, r.idxmax().date()))
print("days |ret|>15%%:", int((r.abs()>0.15).sum()), " |ret|>10%%:", int((r.abs()>0.10).sum()))
print("dates falling on weekend:", [(d.date(), f"{v*100:.3f}%") for d,v in r.items() if d.weekday()>=5][:20])

# ---- NYSE calendar reconstruction (no external libs) ----
def easter(year):
    a=year%19; b=year//100; c=year%100; d_=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d_-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
    return dt.date(year,month,day)

def nsew_holidays(year):
    H=set()
    def obs(d0):  # Saturday->Fri before, Sunday->Mon after
        if d0.weekday()==5: return d0-dt.timedelta(days=1)
        if d0.weekday()==6: return d0+dt.timedelta(days=1)
        return d0
    H.add(obs(dt.date(year,1,1)))
    if year>=1998: # MLK 3rd Monday Jan
        d=dt.date(year,1,1); H.add(d+dt.timedelta(days=(7-d.weekday())%7+14))
    # Washington 3rd Monday Feb
    d=dt.date(year,2,1); H.add(d+dt.timedelta(days=(7-d.weekday())%7+14))
    H.add(easter(year)-dt.timedelta(days=2))  # Good Friday
    d=dt.date(year,5,31); H.add(d-dt.timedelta(days=d.weekday()))  # Memorial last Mon
    if year>=2022: H.add(obs(dt.date(year,6,19)))  # Juneteenth
    H.add(obs(dt.date(year,7,4)))
    d=dt.date(year,9,1); H.add(d+dt.timedelta(days=(7-d.weekday())%7))  # Labor
    d=dt.date(year,11,1); H.add(d+dt.timedelta(days=(7-d.weekday())%7+21))  # Thanksgiving 4th Thu
    H.add(obs(dt.date(year,12,25)))
    if year==2012: H.add(dt.date(2012,10,29)); H.add(dt.date(2012,10,30))  # Sandy
    if year==2018: H.add(dt.date(2018,12,5))   # Bush 41 day of mourning
    if year==2025: H.add(dt.date(2025,1,9))    # Carter day of mourning
    return H

start, end = r.index[0].date(), r.index[-1].date()
allDays = pd.date_range(start, end, freq="D")
closed = set()
for y in range(start.year, end.year+1):
    for h in nsew_holidays(y):
        closed.add(pd.Timestamp(h))
nyse_open = [d for d in allDays if d.weekday()<5 and d not in closed]
nyse_open = pd.DatetimeIndex(nyse_open)
print(f"\n== NYSE calendar (reconstructed, no libs) ==")
print(f"NYSE open days {start}..{end}: {len(nyse_open)}; CSV rows: {len(r)}")

in_csv_not_nyse = [d for d in r.index if d not in set(nyse_open)]
print(f"CSV dates that are NOT NYSE open days: {len(in_csv_not_nyse)}")
for d in in_csv_not_nyse[:25]:
    v=r.loc[d]; print(f"   {d.date()} ({d.day_name()}) ret={v*100:.4f}%")

missing = [d for d in nyse_open if d not in set(r.index)]
print(f"NYSE open days MISSING from CSV: {len(missing)}")
for d in missing[:40]:
    print(f"   {d.date()} ({d.day_name()})")
