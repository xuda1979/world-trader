import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

ng = L.newdata('DHHNGSP')
rl = L.logret(ng); idx = rl.index
m_end = idx.to_series().groupby(idx.to_period('M')).max()   # last trading day per month
# rank of day within month (business days present)
def day_rank(ts):
    mon = idx[idx.to_period('M') == ts.to_period('M')]
    return list(mon).index(ts), len(mon)
# vectorized: ordinal within month
ordr = idx.to_series().groupby(idx.to_period('M')).cumcount()
sizes = idx.to_series().groupby(idx.to_period('M')).transform('size')
ordr.index, sizes.index = idx, idx
last3 = ordr >= sizes - 3      # last 3 bdays of month (incl final)
last2 = ordr >= sizes - 2
last1 = ordr >= sizes - 1
first5 = ordr < 5

print("raw mean ret bp/d by month-position:")
for nm, mask in [('last1', last1), ('last2', last2), ('last3', last3), ('first5', first5), ('mid', ~(last3|first5))]:
    x = rl[mask]
    t = x.mean()/x.std()*np.sqrt(len(x))
    print(f"  {nm}: n={len(x)} ann {x.mean()*252*1e4:.0f}bp t {t:.2f}")

# Book A: long last-3-bd, flat otherwise; Book B: long last3 short first5; Book C: short last3 long first5
def book(mask_long, mask_short=None):
    pos = pd.Series(0.0, index=idx)
    pos[mask_long] = 1.0
    if mask_short is not None: pos[mask_short] = -1.0
    net = L.vt10(L.net_turnover(pos, rl))
    s = L.full_stats(net); h1,h2 = L.halves_sr(net)
    cb,cc,n = L.corr_blend(net)
    print(f"  -> SR {s['sr']:.2f} ann {s['ann']:.1f}% MDD {s['mdd']:.1f}% negy {s['negy']}/{s['years']} worst {s['worst']:.1f}% H1 {h1:.2f} H2 {h2:.2f} corrB {cb:.3f}")

print("Book long last3 only:"); book(last3)
print("Book short last3 / long first5:"); book(~first5 & ~last3 & pd.Series(False,index=idx) if False else first5, last3)
print("Book long last3 / short first5:"); book(last3, first5)
print("Book long first5 only:"); book(first5)

# refine: separate last3 into day -3,-2,-1
for k in [1,2,3]:
    m = ordr >= sizes - k
    x = rl[m]; t = x.mean()/x.std()*np.sqrt(len(x))
    print(f"  last{k}: ann {x.mean()*252*1e4:.0f}bp t {t:.2f}")
# also check first 3 individually
for k in [0,1,2]:
    m = ordr == k
    x = rl[m]; t = x.mean()/x.std()*np.sqrt(len(x))
    print(f"  bd{k}: ann {x.mean()*252*1e4:.0f}bp t {t:.2f}")
