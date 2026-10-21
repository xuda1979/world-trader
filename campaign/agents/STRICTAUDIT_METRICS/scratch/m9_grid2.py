# m9: identify the 264 excluded days precisely; cross-tab 89 dropped open days by absent sleeves
import pandas as pd, numpy as np, datetime as dt
B="/Users/daxu/software/world-trader"
SLEEVES = {
 'brwt15': f"{B}/campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
 'brwt10': f"{B}/campaign/agents/COORD/sleeves/brwt10_2000.csv",
 'brwt7':  f"{B}/campaign/agents/COORD/sleeves/brwt7.csv",
 'brwt5':  f"{B}/campaign/agents/COORD/sleeves/brwt5.csv",
 'C5ng':   f"{B}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 'C5ngsum':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 'A5r2':   f"{B}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
 'a6r7':   f"{B}/campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 'QAxasts':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189_2006.csv",
 'carryv2':f"{B}/campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 'dualmom':f"{B}/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
 'XGB1y':  f"{B}/campaign/results/sleeve_library/XGB1y_deploy.csv",
}
P={}
for k,p in SLEEVES.items():
    s=pd.read_csv(p,parse_dates=['date']).set_index('date')['ret']
    P[k]=pd.to_numeric(s,errors='coerce')
ch=pd.read_csv(f"{B}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv",index_col=0,parse_dates=True)['ret']
win=ch.index; cset=set(win)

def easter(year):
    a=year%19; b=year//100; c=year%100; d_=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d_-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    month=(h+l-7*m+114)//31; day=((h+l-7*m+114)%31)+1
    return dt.date(year,month,day)
def nth(y,mo,wd,n):
    d=dt.date(y,mo,1); return d+dt.timedelta(days=(wd-d.weekday())%7+7*(n-1))
def last(y,mo,wd):
    d=dt.date(y,mo+1,1)-dt.timedelta(days=1) if mo<12 else dt.date(y,12,31)
    return d-dt.timedelta(days=(d.weekday()-wd)%7)
def obs(d0):
    if d0.weekday()==5: return d0-dt.timedelta(days=1)
    if d0.weekday()==6: return d0+dt.timedelta(days=1)
    return d0
closed=set()
for y in range(win[0].year,win[-1].year+1):
    H={obs(dt.date(y,1,1)),nth(y,1,0,3),nth(y,2,0,3),easter(y)-dt.timedelta(days=2),last(y,5,0),
       obs(dt.date(y,7,4)),nth(y,9,0,1),nth(y,11,3,4),obs(dt.date(y,12,25))}
    if y>=2022: H.add(obs(dt.date(y,6,19)))
    if y==2012: H|={dt.date(2012,10,29),dt.date(2012,10,30)}
    if y==2011: H.add(dt.date(2011,8,29))
    if y==2018: H.add(dt.date(2018,12,5))
    if y==2025: H.add(dt.date(2025,1,9))
    for h in H: closed.add(pd.Timestamp(h))
def is_open(d): return d.weekday()<5 and d not in closed

allgrid = set()
for k in P: allgrid |= set(P[k].dropna().index)
allgrid = {d for d in allgrid if win[0]<=d<=win[-1]}
missing = sorted(allgrid - cset)          # >=1 sleeve has data, champion excludes
open_missing = [d for d in missing if is_open(d)]
closed_missing = [d for d in missing if not is_open(d)]
print(f"union-grid days in window: {len(allgrid)}; champion: {len(cset)}; excluded: {len(missing)}")
print(f"  excluded AND NYSE-open: {len(open_missing)}  (these = the 89-ish vendor-hole days)")
print(f"  excluded AND NYSE-closed: {len(closed_missing)} (holidays where some sleeve has rows)")
champ_closed = [d for d in win if not is_open(d)]
print(f"  champion rows on NYSE-closed days: {len(champ_closed)}")
if champ_closed: print("   ", [(str(d.date()), d.day_name()) for d in champ_closed[:10]])

print("\n== the dropped OPEN days: how many sleeves have data on each? ==")
from collections import Counter
cnt = Counter()
for d in open_missing:
    n_present = sum(d in set(P[k].dropna().index) for k in P)
    cnt[n_present]+=1
print("  (#sleeves present -> #days):", dict(sorted(cnt.items())))
for d in open_missing:
    n_present = sum(d in set(P[k].dropna().index) for k in P)
    if n_present>0:
        present=[k for k in P if d in set(P[k].dropna().index)]
        print(f"   {d.date()} ({d.day_name()}): {n_present} present: {present}")

print("\n== the excluded CLOSED days: sleeves present on holidays? ==")
cnt2 = Counter()
for d in closed_missing:
    n_present = sum(d in set(P[k].dropna().index) for k in P)
    cnt2[n_present]+=1
print("  (#sleeves present -> #days):", dict(sorted(cnt2.items())))
one = [d for d in closed_missing if sum(d in set(P[k].dropna().index) for k in P)==1]
print(f"  holidays where only 1 sleeve has a row: {len(one)}; sample:", [str(d.date()) for d in one[:8]])
print(f"  which sleeve? ", Counter(k for d in one for k in P if d in set(P[k].dropna().index)))
