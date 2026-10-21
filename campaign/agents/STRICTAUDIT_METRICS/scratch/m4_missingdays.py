# m4: (a) verify easter/2011 rows; (b) are the 89 missing days vendor holes? SPY check; (c) day-count materiality
import pandas as pd, numpy as np, datetime as dt

CSV = "/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r = pd.read_csv(CSV, index_col=0, parse_dates=True).iloc[:,0].sort_index()

def easter(year):
    a=year%19; b=year//100; c=year%100; d_=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d_-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
    return dt.date(year,month,day)
for y in [2011, 2020, 2026]:
    print(f"easter {y}: {easter(y)} (Good Friday {easter(y)-dt.timedelta(days=2)})")

print("\nCSV rows around Easter 2011:")
for d in pd.date_range("2011-04-18","2011-05-02"):
    v = r.get(d, np.nan)
    print(f"  {d.date()} {d.day_name()}: {'' if pd.isna(v) else f'{v*100:+.4f}%'}{'   <-- MISSING' if pd.isna(v) else ''}")

# SPY check
spy = pd.read_csv("/Users/daxu/software/world-trader/tools/quant/data/twelvedata/SPY.csv")
print("\nSPY(twelvedata) cols:", list(spy.columns)[:6], "n=", len(spy))
dc = spy.columns[0]
spy[dc] = pd.to_datetime(spy[dc])
spy = spy.set_index(dc).sort_index()
spy = spy[(spy.index>=r.index[0]) & (spy.index<=r.index[-1])]
print(f"SPY rows in window: {len(spy)} vs CSV {len(r)}")
missing = pd.DatetimeIndex([d for d in pd.date_range(r.index[0], r.index[-1], freq='D')
        if d.weekday()<5 and d not in set(r.index) and d in set(spy.index)])
# SPY-open days missing from CSV:
spy_open = set(spy.index)
csv_open = set(r.index)
win = [d for d in spy_open if r.index[0]<=d<=r.index[-1]]
miss2 = sorted(win - csv_open)
print(f"days where SPY has data but CSV missing: {len(miss2)}")
for d in miss2[:20]: print("   ", d.date())
extra = sorted(csv_open - set(win))
print(f"days CSV has but SPY missing: {len(extra)}", [str(d.date()) for d in extra[:10]])
# SPY return on the missing days: real market moves the CSV skips
sret = spy.iloc[:, spy.columns.get_loc('close') if 'close' in spy.columns else 4].pct_change()
mm = [d for d in miss2]
vals = [sret.get(d, np.nan) for d in miss2]
vals = pd.Series(vals, index=pd.DatetimeIndex(miss2)).dropna()
print(f"\nSPY |ret| on CSV-missing days: mean {vals.abs().mean()*100:.3f}%, max {vals.abs().max()*100:.2f}% on {vals.abs().idxmax().date()}")
print(f"SPY days missing from CSV with |move|>1%: {int((vals.abs()>0.01).sum())}")
for d,v in vals[vals.abs()>0.01].items(): print(f"   {d.date()}: SPY {v*100:+.2f}%")

# materiality: what ann would be if 252 -> observed-per-year scaling
n=len(r); yrs=(r.index[-1]-r.index[0]).days/365.25
print(f"\nobserved days/yr: {n/yrs:.2f}; NYSE ~251.5; ann=mu*252 relative overstatement if true freq is obs/yr: {252/(n/yrs)*100-100:+.1f}%")
