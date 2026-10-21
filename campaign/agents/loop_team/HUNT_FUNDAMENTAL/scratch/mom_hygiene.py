"""Momentum under graded hygiene. Q2 = drop |r|>50%; Q3 = drop |r|>25%.
PnL always on winsorized[-50,+50] returns. Momentum signal itself also winsorized."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad50 = (rets_raw.abs() > 0.50)
bad25 = (rets_raw.abs() > 0.25)

def build(sigfn, dates, lf, sf, lev, drop=None):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    if drop is not None:
        bad_tr = drop.rolling(504, min_periods=1).max().shift(1).fillna(0.0)
    else:
        bad_tr = pd.DataFrame(0.0, index=idx, columns=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
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
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    sn = -(W.clip(upper=0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4 - sn*BORROW/252
    return net, W

def momsig(t, lb=252, skip=21, wins=True):
    m = (px.shift(skip)/px.shift(lb)-1).loc[t]
    return m.clip(-0.95, 3.0) if wins else m

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
configs = [
    ("no drop, full panel", None, 1/3, 2.0),
    ("Q2 drop|50%|, full", bad50, 1/3, 2.0),
    ("Q3 drop|25%|, full", bad25, 1/3, 2.0),
    ("Q3 drop|25%|, liquid-298 only", bad25, 1/3, 2.0),
]
for name, drop, frac, lev in configs:
    if "liquid" in name:
        import os
        d1 = "/Users/daxu/software/world-trader/tools/quant/data/twelve_big"
        big = set(fn[:-4] for fn in os.listdir(d1) if fn.endswith('.csv'))
        keep = [c for c in px.columns if c in big]
    else:
        keep = None
    def sf(t, frac=frac, keep=keep):
        m = momsig(t)
        if keep is not None:
            m = m.where(m.index.isin(keep))
        return m
    net, W = build(sf, mes, frac, 0.0, lev, drop=drop)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    print(f"{name:32s}: SR={sr:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} worst={yr.min():+.1%} vol={r.std()*np.sqrt(252):.1%}")
