"""E2 Idea 3: Treasury refunding-cycle bond books. Quarterly refunding announcements =
first business Wednesday of Feb/May/Aug/Nov (rule-based). Proxy book on 10y TR synth."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import e2_lib as L, numpy as np, pandas as pd

y10 = L.D.fred("DGS10") / 100.0
y10 = y10.dropna()
r10 = -0.0/1.0  # placeholder
# TR approximation: ret_t = ytm_{t-1}/252*? Use classic approx: TR = yld carry - dur*d(y)
# carry: use current yield /252 annualized? Standard: ret = (y/252) - D*dy with D=8.5
dy = y10.diff()
carry = y10.shift(1) / 252.0
tr = (carry - 8.5 * dy.shift(-1))  # earning day t+1 uses y at t (carry) and y-change t->t+1
tr = tr.dropna()
cal = tr.index
print("10y TR synth:", cal.min().date(), cal.max().date(), len(cal), "ann vol", round(tr.std()*np.sqrt(252)*100,1))

# refunding announcement days: first business Wednesday of Feb/May/Aug/Nov
ann_days = []
for y in range(1990, 2027):
    for m in (2,5,8,11):
        d = pd.Timestamp(y, m, 1)
        add = (2 - d.dayofweek) % 7   # Wednesday=2
        ann_days.append(d + pd.Timedelta(days=add))
ann_days = pd.DatetimeIndex(ann_days)
ann_days = ann_days[(ann_days >= cal.min()) & (ann_days <= cal.max())]
# map to nearest trading day
caln = cal.values.astype('datetime64[D]'); ann = ann_days.values.astype('datetime64[D]')
dist = np.busday_count(caln[:,None], ann[None,:]).astype(np.int64)   # day -> announcement (>=0)
near = np.abs(dist).argmin(axis=0)
ann_trading = pd.Series(dist[near, np.arange(len(ann))], index=ann)

def pos_for(a, b, sign):
    return sign * ((ann_trading >= a) & (ann_trading <= b)).reindex(cal).fillna(0.0).astype(float)

print("\ngrid: window [a,b] relative to announcement day; L and S")
rows=[]
for a,b in [(-5,-1),(-3,-1),(-1,0),(0,1),(0,3),(1,3),(0,5),(-5,3),(-2,2),(-1,1),(-5,-2),(4,10),(5,15)]:
    for sign,lab in [(1,'L'),(-1,'S')]:
        net = L.book_net(pos_for(a,b,sign), tr)
        s = L.full_stats(net)
        rows.append((a,b,lab,round(s['sr'],2),round(s['ann'],1),round(s['vol'],1),s['negy']))
df = pd.DataFrame(rows, columns=['a','b','side','sr','ann','vol','negy']).sort_values('sr',ascending=False)
print(df.head(10).to_string())
print("...")
print(df.tail(4).to_string())

# event study on announcement-day direction
print("\nevent study: 10y yield change on announcement day (bp)")
ev = y10.diff().reindex(cal)
d0 = pd.Series(dist.min(axis=1)==0, index=cal)
print("ann-day dy:", round(ev[d0].mean()*1e4,2), "bp, n=", d0.sum(), "| other:", round(ev[~d0].mean()*1e4,2))
print("by side: yields UP on ann days?", (ev[d0]>0).mean().round(3))
