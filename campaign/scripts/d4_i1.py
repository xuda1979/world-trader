import sys; sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/D4_microstruct')
import d4_lib as L
import numpy as np, pandas as pd

ng = L.newdata('DHHNGSP'); xau = L.price('xau')
f = pd.read_csv(f"{L.NEWDATA}/fomc_dates.csv", parse_dates=True)
all_d = pd.to_datetime(pd.concat([f['day1'], f['day2']]).dropna())
fomc = sorted(set(all_d.dt.normalize()))
print("FOMC meetings:", len(f), "unique dates:", len(fomc), fomc[0].date(), fomc[-1].date())

# day types relative to FOMC: day2 = decision day (last), day1 = eve
rl_ng, rl_au = L.logret(ng), L.logret(xau)
dts = rl_ng.index
fset = set(fomc)
def daytype(ts):
    d = ts.normalize()
    nxt = ts + pd.Timedelta(days=1); nxtb = nxt
    while nxtb not in dts and (nxtb - d).days < 5: nxtb += pd.Timedelta(days=1)
    is_next_fomc = nxtb.normalize() in fset
    if d in fset and (d + pd.Timedelta(days=1)) not in fset: return 'dec'  # 2nd day (decision close)
    if d in fset: return 'eve'  # 1st day
    if is_next_fomc: return 'pre'
    return 'norm'
typ = pd.Series([daytype(t) for t in dts], index=dts)
print(typ.value_counts())

# Phase A: unconditional mean |ret| by day type (natgas & gold)
for nm, rl in [('NG', rl_ng), ('AU', rl_au)]:
    stats_d = rl.groupby(typ).agg(['mean','std','count'])
    stats_d['mean_bp'] = stats_d['mean']*1e4
    print(nm); print(stats_d[['mean_bp','std','count']].round(2))
