"""FINAL candidate: HF_mom_cheap — 12-1 momentum LO, cheap-half filter, Q3 hygiene.
Emits TRUE daily series. Full gate battery run here."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

def build():
    idx = px.index
    mes = [pd.Timestamp(d) for d in month_ends(idx)]
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(mes):
        m = ((px.shift(21)/px.shift(252)-1).loc[t]).clip(-0.95, 3.0)
        v = sigv.loc[t].dropna()
        if len(v) >= 20:
            m = m.where(v.le(v.quantile(0.5)).reindex(px.columns).fillna(False))
        row = m.dropna()
        row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); nl = max(int(np.floor(len(rs)/2)),1)
            neww = pd.Series(1.0/nl, index=rs.index[-nl:]).reindex(px.columns).fillna(0.0)
        nxt = mes[k+1] if k+1<len(mes) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4
    return net, W, turn

net, W, turn = build()
r = vol_target(net, 0.10).iloc[5:].dropna()
r = r[r.index >= '2009-07-01']
print("=== HF_mom_cheap full gates ===")
ok, g = full_gates(r, "HF_mom_cheap")
fg = flatten_gate(r)
print("flatten gate:", fg, "PASS" if fg["pass_"] else "FAIL")
print("avg names:", int((W>0).sum(axis=1).mean()), "turn bps/d:", round(turn.mean()*6,2))
print("vol:", round(r.std()*np.sqrt(252)*100,1), "%")
r.to_frame("ret").to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/HF_mom_cheap_daily.csv")
print("saved scratch/HF_mom_cheap_daily.csv n=", len(r))
