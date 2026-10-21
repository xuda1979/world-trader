# m10: (a) gap-folding evidence; (b) zero-fill materiality on full NYSE grid; (c) monthly DD;
#      (d) pairwise sleeve correlations & effective N; (e) top-day concentration; (f) sibling-file diffs
import pandas as pd, numpy as np, datetime as dt
B="/Users/daxu/software/world-trader"
CSV=f"{B}/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r=pd.read_csv(CSV,index_col=0,parse_dates=True)['ret'].dropna()

def easter(year):
    a=year%19; b=year//100; c=year%100; d_=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
    h=(19*a+b-d_-g+15)%30; i=c//4; k=c%4; l=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*l)//451
    return dt.date(year,(h+l-7*m+114)//31,((h+l-7*m+114)%31)+1)
def nth(y,mo,wd,n):
    d=dt.date(y,mo,1); return d+dt.timedelta(days=(wd-d.weekday())%7+7*(n-1))
def last(y,mo,wd):
    d=dt.date(y,mo+1,1)-dt.timedelta(days=1) if mo<12 else dt.date(y,12,31)
    return d-dt.timedelta(days=(d.weekday()-wd)%7)
def obs(d0):
    return d0-dt.timedelta(days=1) if d0.weekday()==5 else (d0+dt.timedelta(days=1) if d0.weekday()==6 else d0)
closed=set()
for y in range(r.index[0].year,r.index[-1].year+1):
    H={obs(dt.date(y,1,1)),nth(y,1,0,3),nth(y,2,0,3),easter(y)-dt.timedelta(days=2),last(y,5,0),
       obs(dt.date(y,7,4)),nth(y,9,0,1),nth(y,11,3,4),obs(dt.date(y,12,25))}
    if y>=2022: H.add(obs(dt.date(y,6,19)))
    if y==2012: H|={dt.date(2012,10,29),dt.date(2012,10,30)}
    if y==2011: H.add(dt.date(2011,8,29))
    if y==2018: H.add(dt.date(2018,12,5))
    if y==2025: H.add(dt.date(2025,1,9))
    closed|={pd.Timestamp(h) for h in H}
nyse=pd.DatetimeIndex([d for d in pd.date_range(r.index[0],r.index[-1]) if d.weekday()<5 and d not in closed])
print(f"NYSE open days: {len(nyse)}; champion rows: {len(r)}; missing open days: {len(set(nyse)-set(r.index))}")

# (a) gap-folding evidence: multi-day skip -> next champion day is multi-day?
rf=pd.Series(r.values, index=r.index).reindex(nyse)  # NaN on the 89 missing
gaplen = rf.isna().astype(int).groupby((~rf.isna()).cumsum()).cumsum()  # count consecutive missing before each present day
skips = rf.isna().astype(int)
nskip_before = pd.Series(0, index=nyse)
c=0
for d in nyse:
    nskip_before[d]=c
    c = c+1 if pd.isna(rf[d]) else 0
after = r[[d for d in r.index if nskip_before[d]>0]]
normal = r[[d for d in r.index if nskip_before[d]==0]][21:]  # skip warmup
print(f"\n(a) after-gap days n={len(after)}: mean={after.mean()*100:+.3f}% std={after.std()*100:.3f}%")
print(f"    normal days n={len(normal)}: mean={normal.mean()*100:+.3f}% std={normal.std()*100:.3f}%")
print(f"    std ratio after/normal = {after.std()/normal.std():.2f}x  (≈1 => PnL NOT folded, gaps are holes; ≈sqrt(2-3) => folded)")
g2 = r[[d for d in r.index if nskip_before[d]>=2]]
print(f"    after 2+ day gaps n={len(g2)}: std={g2.std()*100:.3f}% vs normal {normal.std()*100:.3f}% -> ratio {g2.std()/normal.std():.2f}x")

# (b) zero-fill materiality
rz = r.reindex(nyse).fillna(0.0)
mu,sd = rz.mean(), rz.std(ddof=1)
print(f"\n(b) zero-filled on 4611-day NYSE grid: ann={mu*252*100:.2f}%  SR={mu/sd*np.sqrt(252):.3f}")
eq=(1+rz).cumprod(); print(f"    MaxDD={((eq/eq.cummax())-1).min()*100:.2f}%")
mz = rz.resample("ME").apply(lambda x:(1+x).prod()-1)
print(f"    monthly SR={mz.mean()/mz.std(ddof=1)*np.sqrt(12):.3f}")
negz = rz.groupby(rz.index.year).apply(lambda x:(1+x).prod()-1)
print(f"    neg years={int((negz<0).sum())}/{len(negz)}  lowest={negz.min()*100:.2f}%")

# (c) monthly-DD (as-committed series)
mm = r.resample("ME").apply(lambda x:(1+x).prod()-1)
em=(1+mm).cumprod(); mdd_m=(em/em.cummax()-1).min()
print(f"\n(c) monthly-equity MaxDD = {mdd_m*100:.2f}%")

# (e) top-day concentration
s=r.sort_values(ascending=False)
tot=r.sum()
top5=s.head(5).sum(); top10=s.head(10).sum(); top20=s.head(20).sum()
print(f"\n(e) total sum of daily rets = {tot*100:.0f}pp; top5 days={top5/tot*100:.1f}% of it; top10={top10/tot*100:.1f}%; top20={top20/tot*100:.1f}%")
print(f"    2020-09-01 (+14.72%) alone = {s.iloc[0]/tot*100:.1f}% of total PnL; without it ann={(r.sum()-s.iloc[0])/len(r)*252*100:.1f}%")
print(f"    without top-5 days: ann={(r.sum()-top5)/len(r)*252*100:.1f}%")

# (f) sibling files
for f in ["GOAL100_IBKR_STRICT_BALANCED_daily.csv","GOAL100_FINAL_TRUTH_BALANCED_daily.csv"]:
    try:
        x=pd.read_csv(f"{B}/campaign/results/{f}",index_col=0,parse_dates=True)['ret'].dropna()
        j=pd.concat([r,x],axis=1,join='inner').dropna()
        print(f"\n(f) vs {f}: common={len(j)} corr={j.corr().iloc[0,1]:.6f} maxdiff={(j.iloc[:,0]-j.iloc[:,1]).abs().max()*1e4:.2f}bp")
    except Exception as e: print(f,"ERR",e)
