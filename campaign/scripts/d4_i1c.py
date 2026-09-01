import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

ng = L.newdata('DHHNGSP')
f = pd.read_csv(f"{L.NEWDATA}/fomc_dates.csv", parse_dates=True)
meet = f.dropna().copy(); meet['day2']=pd.to_datetime(meet['day2'])
dec = sorted(pd.to_datetime(meet['day2']).dt.normalize())
rl = L.logret(ng); idx = rl.index

def book(k, side=-1, calm=None):
    pos = pd.Series(0.0, index=idx)
    sig90 = rl.rolling(90).std()
    for dd in dec:
        after = idx[idx > dd][:k]
        ok = pd.Series(True, index=after)
        if calm: ok = rl[after].abs() < calm*sig90[after]
        pos[after[ok.fillna(False)]] = side
    net = L.net_turnover(pos, rl)
    return L.vt10(net), pos

print("SHORT post-FOMC natgas (net, VT10):")
for k in [1,2,3]:
    for calm in [None, 2.5]:
        net,_ = book(k, -1, calm)
        s = L.full_stats(net); h1,h2 = L.halves_sr(net)
        cb,cc,n = L.corr_blend(net)
        print(f"k={k} calm={calm}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f}")

# conditional: long only if pre-FOMC 10d vol compressed (z<0), short drift otherwise
sig = rl.rolling(10).std(); z = (sig - sig.rolling(252).mean())/sig.rolling(252).std()
for k in [1,2]:
    pos = pd.Series(0.0, index=idx)
    for dd in dec:
        after = idx[idx > dd][:k]
        zz = z[after]
        pos[after] = np.where(zz < 0, -1.0, -0.5)  # compressed -> full short, else half
    net = L.vt10(L.net_turnover(pos, rl)); s = L.full_stats(net)
    print(f"cond k={k}: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}%")

# gold decision-window long (eve close -> dec close) quick check
xau = L.price('xau'); rla = L.logret(xau); ia = rla.index
fset = set()
for _, r in meet.iterrows():
    fset.add(pd.Timestamp(r['day1']).normalize()); fset.add(pd.Timestamp(r['day2']).normalize())
pos = pd.Series(0.0, index=ia)
# day1 = 2nd-to-last fomc day before day2; enter at close of first fomc day, earn dec-day return
d1 = sorted(pd.to_datetime(meet['day1']).dt.normalize())
for dd in d1:
    after = ia[ia > dd][:1]
    pos[after] = 1.0
net = L.vt10(L.net_turnover(pos, rla)); s = L.full_stats(net)
print(f"AU dec-day long: SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']}")
