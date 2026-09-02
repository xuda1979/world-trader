"""Momentum with per-name return guard: exclude names whose trailing data contains
bad prints (|ret|>50% ever, or (|ret|>25% more than 3x)). Also winsorize daily rets
at [-50%, +50%] for PnL (crash-conservative). Compare guarded vs unguarded."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
GUARD = 0.50
rets_w = rets_raw.clip(-GUARD, GUARD)          # winsorized PnL
bad = (rets_raw.abs() > 0.50)
# trailing bad-print flag: name excluded from book if it had a bad print in last 504d
bad_tr = bad.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

def build(sigfn, dates, lf, sf, lev, use_guard=True, wt_guard=True):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
        if use_guard:
            row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n*lf)),1); ns = max(int(np.floor(n*sf)),1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:])
            sw = pd.Series(1.0/ns, index=rs.index[:ns]) if sf>0 else None
            neww = lw if sw is None else lw.subtract(sw, fill_value=0.0)
            neww = neww.reindex(px.columns).fillna(0.0)*lev/2.0
        nxt = dates[k+1] if k+1<len(dates) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    rets_use = rets_w if wt_guard else rets_raw
    gross = (W*rets_use.fillna(0.0)).sum(axis=1)
    sn = -(W.clip(upper=0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4 - sn*BORROW/252
    return net, W

def momsig(t, lb=252, skip=21):
    return (px.shift(skip)/px.shift(lb)-1).loc[t]

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
for guard in (False, True):
    net, W = build(momsig, mes, 1.0, 0.0, 1.0, use_guard=guard, wt_guard=guard)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"guard={guard}: SR={r.mean()/r.std()*np.sqrt(252):+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} "
          f"negy={int((yr<0).sum())} worst={yr.min():+.1%} vol={r.std()*np.sqrt(252):.1%}")
    # top-half only
    net2, W2 = build(lambda t: momsig(t), mes, 0.5, 0.0, 1.0, use_guard=guard, wt_guard=guard)
    r2 = vol_target(net2).iloc[5:].dropna(); r2 = r2[r2.index>='2009-07-01']
    print(f"   top-half guard={guard}: SR={r2.mean()/r2.std()*np.sqrt(252):+.2f} ann={(1+r2).prod()**(252/len(r2))-1:+.1%}")
