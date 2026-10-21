# m12: after-gap outlier control + small remaining checks
import pandas as pd, numpy as np
CSV="/Users/daxu/software/world-trader/campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv"
r=pd.read_csv(CSV,index_col=0,parse_dates=True)['ret'].dropna()
# reconstruct after-gap set (89 holes; next-day rows after each hole)
holes=[]
prev=None
for d in r.index:
    if prev is not None and (d-prev).days>3:  # gap over weekend could be 1-4 days; count calendar days skipped that are weekdays
        # crude: any gap where >1 weekday skipped
        import datetime as dt
        wk=sum(1 for i in range(1,(d-prev).days) if (prev+pd.Timedelta(days=i)).weekday()<5)
        if wk>0: holes.append(d)
    prev=d
print(f"days following a skipped-weekday gap: {len(holes)}")
a=r[holes]
a_no=a.drop(pd.Timestamp('2020-09-01'),errors='ignore')
normal=r[~r.index.isin(holes)][21:]
print(f"after-gap mean={a.mean()*100:+.3f}% std={a.std()*100:.3f}%; EXCL 2020-09-01: mean={a_no.mean()*100:+.3f}% std={a_no.std()*100:.3f}%")
print(f"normal mean={normal.mean()*100:+.3f}% std={normal.std()*100:.3f}%")
print(f"std ratio after-gap/normal excl outlier: {a_no.std()/normal.std():.2f}")
print(f"t-test mean(after-gap) vs mean(normal): diff={a_no.mean()*100:+.3f}pp, se={np.sqrt(a_no.var()/len(a_no)+normal.var()/len(normal))*100:.3f}pp")
print(f"min |ret|: {r.abs().min()*1e4:.4f} bp; days |ret|<1e-6: {(r.abs()<1e-6).sum()}")
# rolling 126d ann vol max/min
vol=r.rolling(126).std()*np.sqrt(252)
print(f"126d rolling ann vol: min={vol.min()*100:.2f}% med={vol.median()*100:.2f}% max={vol.max()*100:.2f}%")
# implied gross (ann/vol check not needed) - 2020-09-01 gross implied: 14.72/0.55 typical-day sd
print(f"2020-09-01 return vs full-sample daily sd: {r.loc['2020-09-01']/r.std():.1f} sigma; vs 126d prior sd: {r.loc['2020-09-01']/(r.loc[:'2020-08-31'].rolling(126).std().iloc[-1]):.1f} sigma")
