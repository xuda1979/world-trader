"""Momentum family gated OFF when dualmom's gate is off — decorrelate from committed sleeve."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd
from campaign.harness import data as D

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

ff = D.ff_factors(); mkt = (1 + ff["Mkt-RF"] + ff["RF"]).cumprod()
ma = mkt.rolling(200, min_periods=200).mean()
g0 = pd.Series(np.where(mkt > ma*1.03, 1.0, np.where(mkt < ma*0.97, 0.0, np.nan)), index=mkt.index)
# T+1 honest: gate known at t applied from t+1
G = g0.reindex(px.index).ffill().fillna(0.0).shift(1).fillna(0.0)

def build(sigfn, dates, lf, sf, lev):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
        row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10 or G.loc[t] <= 0:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n*lf)),1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:])
            neww = lw.reindex(px.columns).fillna(0.0)*lev/2.0
        nxt = dates[k+1] if k+1<len(dates) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4
    return net, W

def momsig(t, lb=252, skip=21):
    return ((px.shift(skip)/px.shift(lb)-1).loc[t]).clip(-0.95, 3.0)
def cheap_mask(t, q):
    v = sigv.loc[t].dropna()
    if len(v) < 20: return pd.Series(False, index=px.columns)
    return v.le(v.quantile(q)).reindex(px.columns).fillna(False)

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
configs = [
    ("G gate+cheap-half", 0.5),
    ("G gate-only full panel", None),
    ("G gate+cheap-tercile", 0.33),
]
out = {}
for name, cq in configs:
    def sfn(t, cq=cq):
        m = momsig(t)
        if cq is not None:
            m = m.where(cheap_mask(t, cq))
        return m
    net, W = build(sfn, mes, 1.0, 0.0, 1.0)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    mid = r.index[len(r)//2]
    sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
    sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
    negs = {int(k): round(v*100,1) for k,v in yr[yr<0].items()}
    print(f"{name:26s}: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} {negs}")
    out[name] = r
pd.DataFrame(out).to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/mom_gate_raw.csv")
print("saved")
