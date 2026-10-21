"""Does the number of names held (top-N) drive the edge? Momentum LO at different widths."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)
idx = px.index
mes = [pd.Timestamp(d) for d in month_ends(idx)]

def build(topfrac, cheap):
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(mes):
        m = ((px.shift(21)/px.shift(252)-1).loc[t]).clip(-0.95, 3.0)
        if cheap:
            v = sigv.loc[t].dropna()
            if len(v) >= 20:
                m = m.where(v.le(v.quantile(0.5)).reindex(px.columns).fillna(False))
        row = m.dropna()
        row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); nl = max(int(np.floor(len(rs)*topfrac)),1)
            neww = pd.Series(1.0/nl, index=rs.index[-nl:]).reindex(px.columns).fillna(0.0)
        nxt = mes[k+1] if k+1<len(mes) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    return r

for frac in (1/12, 1/6, 1/3, 1/2, 2/3, 1.0):
    for cheap in (False, True):
        r = build(frac, cheap)
        print(f"topfrac={frac:.2f} cheap={cheap}: SR={r.mean()/r.std()*np.sqrt(252):+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%}")
