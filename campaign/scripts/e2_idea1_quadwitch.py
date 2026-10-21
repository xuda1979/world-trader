"""E2 Idea 1+2: quad-witching / opex-week SPX books. T+1, 6bps/side."""
import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
import e2_lib as L, numpy as np, pandas as pd

ret = L.spy_ret()
# quad-witching Friday F = 3rd Friday of Mar/Jun/Sep/Dec (weekly index opts expire 3rd Fri;
# if 3rd Fri is a holiday, expiry is Thursday — approximate with actual trading calendar:
cal = pd.DatetimeIndex(sorted(set(ret.index)))
qw = []
for y in range(cal.year.min(), cal.year.max()+1):
    for m in (3,6,9,12):
        qw.append(L.nth_weekday(y, m, 4, 3))
qw = pd.DatetimeIndex(qw)
# map each calendar-known earning day to offset relative to next quad Friday
qw_sorted = qw.sort_values()
# for each trading day t, find covering quad cycle: offsets -10..+10 relative to F
off = pd.Series(index=cal, dtype=float)
for f in qw_sorted:
    for k in range(-10, 11):
        d = f + pd.Timedelta(days=k)
        # offset by TRADING days: count business days between
        pass
# simpler: use numpy busday offset
import numpy as np
caln = cal.values.astype('datetime64[D]')
qwn = qw_sorted.values.astype('datetime64[D]')
# busday_offset(start, end): business-day count from start to end; nearest quad F dist:
da = np.busday_count(qwn[:,None], caln[None,:]).astype(np.int64)  # (nF, nDays) SIGNED bus-day dist F->day
nearest = np.abs(da).argmin(axis=0)                                # nearest quad F per day
off = pd.Series(da[nearest, np.arange(len(cal))], index=cal)       # signed offset, +after/-before

def window_pos(a, b, sign=1.0):
    """long earning days t with a <= t_off <= b (offsets relative to quad F, b may be negative)."""
    return sign*((off >= a) & (off <= b)).astype(float)

print("=== IDEA 1: quad-witching windows, SPY long/cash (grid) ===")
rows=[]
for a,b in [(-5,-1),(-4,-1),(-3,-1),(-5,0),(-4,0),(-5,3),(-4,3),(-5,5),(0,0),(0,3),(1,4),(-3,3),(-1,1),(-1,3)]:
    for sign,lab in [(1,'L'),(-1,'S')]:
        pos = window_pos(a,b,sign)
        net = L.book_net(pos, ret)
        for start in (None, '2006-09-26'):
            r = net[net.index>=pd.Timestamp(start)] if start else net
            # raw stats (no VT for grid; VT won't rescue sub-1 SR)
            s = L.full_stats(r)
            rows.append((a,b,lab,start or 'full', round(s['sr'],2), round(s['ann'],1), round(s['vol'],1)))
df = pd.DataFrame(rows, columns=['a','b','side','win','sr','ann','vol'])
print(df.sort_values('sr',ascending=False).head(12).to_string())
print("...worst:"); print(df.sort_values('sr').head(3).to_string())

print("\n=== IDEA 2: opex-day vs other days (daily stats) ===")
d = ret.to_frame('r'); d['opex'] = (off==0).astype(float)
# opex day return = earning day t with off==0 => pos on that day
grp = d.groupby('opex')['r']
m = grp.mean()*1e4; sd = grp.std()*1e4; n = grp.count()
t = (m[1]-m[0])/(d['r'].std()*1e4)*np.sqrt(len(d))
print(f"opex-day mean={m[1]:.2f}bp n={int(n[1])} | other={m[0]:.2f}bp | diff t={t:.2f}")
for lo,hi in [(-1,1),(-5,-1),(1,4),(-5,5)]:
    msk = (off>=lo)&(off<=hi)
    print(f"window [{lo},{hi}] mean={d.loc[msk,'r'].mean()*1e4:.2f}bp n={msk.sum()} vs out {d.loc[~msk,'r'].mean()*1e4:.2f}bp")

print("\n=== best cells full gates (incl VT, scramble, corr) ===")
best = df.sort_values('sr',ascending=False).head(3)
for _,row in best.iterrows():
    pos = window_pos(int(row.a), int(row.b), 1.0 if row.side=='L' else -1.0)
    net = L.book_net(pos, ret)
    L.evaluate(net, f"qw_{row.side}_{int(row.a)}_{int(row.b)}")
