"""Final candidate tuning: best fundamental-conditioned momentum books under Q3 hygiene."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

def build(sigfn, dates, lf, sf, lev):
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

def momsig(t, lb, skip):
    return ((px.shift(skip)/px.shift(lb)-1).loc[t]).clip(-0.95, 3.0)
def cheap_mask(t, q):
    v = sigv.loc[t].dropna()
    if len(v) < 20: return pd.Series(False, index=px.columns)
    return v.le(v.quantile(q)).reindex(px.columns).fillna(False)
def pio_mask(t):
    p = sigp.loc[t].dropna()
    if len(p) < 20: return pd.Series(False, index=px.columns)
    return p.ge(p.median()).reindex(px.columns).fillna(False)

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
# candidate grid around (lb=252,skip=21) LO with value filter, and quarterly rebal to cut turnover/corr
configs = [
    ("A mom252L cheap-half M",   252, 21, 0.5, "M", 1.0, 0.0),
    ("B mom252L cheap-half Q",   252, 21, 0.5, "Q", 1.0, 0.0),
    ("C mom252L pio-half M",     252, 21, None, "M", 1.0, 0.0),
    ("D mom126L cheap-half M",   126, 21, 0.5, "M", 1.0, 0.0),
    ("E mom252L full M",         252, 21, None, "M", 1.0, 0.0),
    ("F mom252L cheap-half M top-half book", 252, 21, 0.5, "M", 0.5, 0.0),
]
out = {}
for name, lb, skip, cq, freq, lf, sf in configs:
    def sfn(t, lb=lb, skip=skip, cq=cq):
        m = momsig(t, lb, skip)
        if cq is not None:
            m = m.where(cheap_mask(t, cq))
        return m
    if freq == "M":
        dates = mes
    else:
        dates = [t for t in mes if t.month in (1,4,7,10)]
    net, W = build(sfn, dates, lf, sf, 1.0)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    mid = r.index[len(r)//2]
    sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
    sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
    negs = {int(k): round(v*100,1) for k,v in yr[yr<0].items()}
    print(f"{name:36s}: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} {negs}")
    out[name] = r
pd.DataFrame(out).to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/mom_final_raw.csv")
print("saved")
