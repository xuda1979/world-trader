"""Clean benchmarks: liquid-only (twelve_big) EW; mom long-only book overlap with dualmom."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
import numpy as np, pandas as pd

px, rets = load_panel()
d1 = "/Users/daxu/software/world-trader/tools/quant/data/twelve_big"
import os
big = [fn[:-4] for fn in os.listdir(d1) if fn.endswith('.csv')]
liq = [c for c in px.columns if c in set(big)]
rets_liq = rets[liq]
# winsorize insane daily moves (OTC stubs even in liquid list? no, big is clean) — report
ew_liq = rets_liq.mean(axis=1)
ew_liq = ew_liq[ew_liq.index>='2009-07-01']
print(f"liquid-298 EW 2009-07+: ann={((1+ew_liq).prod()**(252/len(ew_liq))-1):+.1%} vol={ew_liq.std()*np.sqrt(252):.1%}")
ew_all = rets.mean(axis=1)
print(f"ALL-738 EW raw: ann={((1+ew_all).prod()**(252/len(ew_all[ew_all.index>='2009-07-01'])))-1:+.1%}")
# median name return as robustness
med_all = rets.median(axis=1)
print(f"ALL-738 MEDIAN: ann={((1+med_all).prod()**(252/len(med_all[med_all.index>='2009-07-01'])))-1:+.1%}")

# mom long-only books: top tercile mom, 1x, monthly — where do returns come from? top-10 vs rest
def momw(t, lb=252, skip=21):
    m = (px.shift(skip)/px.shift(lb)-1).loc[t]
    return m
mes = [pd.Timestamp(d) for d in month_ends(px.index)]
# average weight on AAPL/MSFT/NVDA etc and OTC names
megas = ['AAPL','MSFT','NVDA','AMZN','GOOGL','META','TSLA']
otc = [c for c in px.columns if c not in set(big)]
cnt_mega, cnt_otc, n_names = 0,0,0
W = pd.DataFrame(0.0, index=px.index, columns=px.columns)
turn = pd.Series(0.0, index=px.index); prev = pd.Series(0.0, index=px.columns)
for k,t in enumerate(mes):
    row = momw(t).dropna()
    if len(row) < 10: continue
    rs = row.sort_values(); nl = max(int(np.floor(len(rs)/3)),1)
    neww = pd.Series(1.0/nl, index=rs.index[-nl:]).reindex(px.columns).fillna(0.0)
    nxt = mes[k+1] if k+1<len(mes) else px.index[-1]
    i0 = px.index.get_loc(t)+1
    if i0>=len(px.index): break
    W.iloc[i0:min(px.index.get_loc(nxt)+1,len(px.index))] = neww.values[None,:]
    turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev = neww
mask_t = W.index >= '2009-07-01'
Wt = W[mask_t]
print("avg names held:", (Wt>0).sum(axis=1).mean().round(1))
print("avg weight on 7 megacaps:", Wt[megas].sum(axis=1).mean().round(3))
print("avg weight on 441 OTC names:", Wt[otc].sum(axis=1).mean().round(3))
gross = (W*rets.fillna(0.0)).sum(axis=1)
net = gross - turn*6e-4
r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
sr = r.mean()/r.std()*np.sqrt(252)
print(f"momL top-tercile: SR={sr:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%}")
# top-10 only
