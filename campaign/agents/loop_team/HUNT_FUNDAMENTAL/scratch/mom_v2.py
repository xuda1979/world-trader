"""mom_v2 grid on UNION panel (64d/126d lookbacks, all timeframes), long-cheap-half only + Q rebalance."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, rets, F, sigv, sigp, mom, report, month_ends, COST_BPS)
import numpy as np, pandas as pd

def build_weights(sigfn, dates, lf, sf, lev):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx)
    prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
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
    gross = (W*rets.fillna(0.0)).sum(axis=1)
    sn = -(W.clip(upper=0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4 - sn*BORROW/252
    return net

def cheap_mom(t, lb, skip, q=0.5):
    m = (px.shift(skip)/px.shift(lb)-1).loc[t]
    v = sigv.loc[t].dropna()
    if len(v) < 20: return pd.Series(np.nan, index=px.columns)
    thr = v.quantile(q)
    cheap = v[v<=thr].index
    return m.where(m.index.isin(cheap))

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
res = []
for lb, skip in [(64,5),(126,21),(189,21),(252,21),(252,126)]:
    net = build_weights(lambda t, lb=lb, skip=skip: cheap_mom(t, lb, skip), mes, 1.0, 0.0, 1.0)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    srq = r[r.index>='2018-01-01']; srq = srq.mean()/srq.std()*np.sqrt(252)
    res.append((lb, skip, sr, srq, (1+r).prod()**(252/len(r))-1, int((yr<0).sum()), yr.min(), r.std()*np.sqrt(252)))
    print(f"lb={lb} skip={skip}: SR={sr:+.2f} SR18+={srq:+.2f} ann={res[-1][4]:+.1%} negy={res[-1][5]} worst={res[-1][6]:+.1%}")
# also full-panel (no value filter) for comparison
for lb, skip in [(126,21),(252,21)]:
    def sf_(t, lb=lb, skip=skip): return (px.shift(skip)/px.shift(lb)-1).loc[t]
    net = build_weights(sf_, mes, 1.0, 0.0, 1.0)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    sr = r.mean()/r.std()*np.sqrt(252)
    srq = r[r.index>='2018-01-01']; srq=srq.mean()/srq.std()*np.sqrt(252)
    print(f"ALL-PANEL lb={lb} skip={skip}: SR={sr:+.2f} SR18+={srq:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%}")
