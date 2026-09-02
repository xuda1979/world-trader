"""Momentum L/S restricted to cheap half (long side) — remove short leg entirely:
mom long among value-cheap + SHORT the panel EW market (hedge).
And: mom long among value-cheap, UNHEDGED (pure long tilt sleeve)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, rets, F, sigv, sigp, mom, report, month_ends, COST_BPS)
import numpy as np, pandas as pd

def run_weights(w, name):
    gross = (w * rets.fillna(0.0)).sum(axis=1)
    sn = -(w.clip(upper=0.0)).sum(axis=1)
    net = gross - sn * BORROW/252   # no rebalance turnover costs here (weights drift)
    return report(name, net, '2009-07-01')

def build(sigfn, lf, sf, lev, freq="ME", gross_fee=0.0):
    idx = px.index
    if freq == "ME":
        dates = list(month_ends(idx))
    else:
        dates = [d for d in idx if d.month in (1,4,7,10)]
    seen=set(); dd=[]
    for d in dates:
        d = pd.Timestamp(d)
        k=(d.year,d.month)
        if k in seen: continue
        seen.add(k); dd.append(d)
    dates = [d for d in dd if d in idx]
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    for k, t in enumerate(dates):
        row = sigfn(t).dropna()
        if len(row) < 10:
            continue
        rs = row.sort_values(); n = len(rs)
        nl = max(int(np.floor(n*lf)),1); ns = max(int(np.floor(n*sf)),1)
        lw = pd.Series(1.0/nl, index=rs.index[-nl:])
        sw = pd.Series(1.0/ns, index=rs.index[:ns]) if sf > 0 else None
        neww = lw if sw is None else lw.subtract(sw, fill_value=0.0)
        neww = neww.reindex(px.columns).fillna(0.0) * lev/2.0
        nxt = dates[k+1] if k+1 < len(dates) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0 >= len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1, len(idx))] = neww.values[None,:]
    return W

# 1) momentum long-only among cheap half, 1x
def sig_mv(t):
    v = sigv.loc[t].dropna()
    m = mom.loc[t]
    if len(v) < 20: return pd.Series(np.nan, index=px.columns)
    cheap = v[v <= v.median()].index
    return m.where(m.index.isin(cheap))
W = build(sig_mv, 1.0, 0.0, 1.0); run_weights(W, "momL@cheap_half_1x")

# 2) same + short panel EW market 1x (beta-hedged) with quarterly rebalance of hedge
mkt = rets.mean(axis=1)
def run_hedged(hedge_w):
    grossL = (W * rets.fillna(0.0)).sum(axis=1)
    net = grossL - hedge_w*mkt - hedge_w*BORROW/252
    r = vol_target(net).iloc[5:].dropna()
    r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    print(f"hedge {hedge_w:.1f}x: SR={sr:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} worst={yr.min():+.1%} vol={r.std()*np.sqrt(252):+.1%}")
for h in (0.0, 0.5, 1.0):
    run_hedged(h)

# 3) long-only value+pio quality tilt (fundamental long-only overlay), 1x
def sig_vp(t):
    v = sigv.loc[t]; p = sigp.loc[t]
    return (v + p).where(v.notna() & p.notna())
W3 = build(sig_vp, 1.0, 0.0, 1.0)
grossL = (W3 * rets.fillna(0.0)).sum(axis=1)
r = vol_target(grossL).iloc[5:].dropna()
r = r[r.index>='2009-07-01']
yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
print(f"value+pio long-only: SR={r.mean()/r.std()*np.sqrt(252):+.2f} ann={((1+r).prod()**(252/len(r))-1):+.1%} vs panel EW same window")
# panel EW same window benchmark
ew = rets.mean(axis=1); ew = ew[(ew.index>='2009-07-01')]
print(f"panel EW: ann={((1+ew).prod()**(252/len(ew))-1):+.1%} vol={ew.std()*np.sqrt(252):+.1%}")
