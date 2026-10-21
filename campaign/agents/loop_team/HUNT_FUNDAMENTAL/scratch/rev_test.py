"""Short-term reversal L/S (weekly), fundamentals-conditioned, Q3 hygiene, union panel."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

def build_rev(sigfn, dates, lf, sf, lev):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
        row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n*lf)),1); ns = max(int(np.floor(n*sf)),1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:])   # HIGH rev score = long
            sw = pd.Series(1.0/ns, index=rs.index[:ns])
            neww = lw.subtract(sw, fill_value=0.0).reindex(px.columns).fillna(0.0)*lev/2.0
        nxt = dates[k+1] if k+1<len(dates) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    sn = -(W.clip(upper=0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4 - sn*BORROW/252
    return net, W, turn

# weekly rebalance: last trading day of each ISO week
idx = px.index
wk = idx.to_series().groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).max()
wk = [pd.Timestamp(d) for d in wk if d in idx]

rev5 = -rets_raw.rolling(5).sum()          # more negative 5d return -> higher score (buy losers)
rev10 = -rets_raw.rolling(10).sum()

def cheap_mask_at(t, q):
    v = sigv.loc[t].dropna()
    if len(v) < 20: return pd.Series(False, index=px.columns)
    return v.le(v.quantile(q)).reindex(px.columns).fillna(False)
def pio_mask_at(t):
    p = sigp.loc[t].dropna()
    if len(p) < 20: return pd.Series(False, index=px.columns)
    return p.ge(p.median()).reindex(px.columns).fillna(False)

import pandas as pd
configs = [
    ("rev5 LS 33/33 lev2", lambda t: rev5.loc[t], 1/3, 1/3, 2.0),
    ("rev5 LS cheap-half lev2", lambda t: rev5.loc[t].where(cheap_mask_at(t,0.5)), 1/3, 1/3, 2.0),
    ("rev5 LS pio-high lev2", lambda t: rev5.loc[t].where(pio_mask_at(t)), 1/3, 1/3, 2.0),
    ("rev5 LS cheap&pio lev2", lambda t: rev5.loc[t].where(cheap_mask_at(t,0.5)&pio_mask_at(t)), 1/3, 1/3, 2.0),
    ("rev10 LS 33/33 lev2", lambda t: rev10.loc[t], 1/3, 1/3, 2.0),
    ("rev5 LS cheap q33 lev3", lambda t: rev5.loc[t].where(cheap_mask_at(t,0.33)), 1/3, 1/3, 3.0),
]
out = {}
for name, sf, lf, sfq, lev in configs:
    net, W, turn = build_rev(sf, wk, lf, sfq, lev)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    if len(r) < 500: print(name, "insufficient"); continue
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    mid = r.index[len(r)//2]
    sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
    sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
    print(f"{name:26s}: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} worst={yr.min():+.1%} turn={turn.mean():.2f}")
    out[name] = r
pd.DataFrame(out).to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/rev_raw.csv")
print("saved")
