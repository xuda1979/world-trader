"""Reversal with DISTRESS FILTER (fundamental screen: exclude distressed names from LONG leg).
Economic rationale: losers bounce (overreaction) unless fundamentals are distressed
(value trap / dead-cat). Distress = negative equity OR pio3<=1 OR accruals extreme."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

# distress flag from fundamentals: pio3 <= 1 (weak profitability/quality)
def pio_scores(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    ta = f2.total_assets.where(lambda s: s > 0)
    roa = f2.net_income / ta
    leg1 = (roa > 0).astype(float).where(f2.net_income.notna())
    leg2 = (roa > roa.groupby(f2.symbol).shift(1)).astype(float).where(f2.net_income.notna())
    shg = f2.shares.groupby(f2.symbol).pct_change()
    leg3 = (shg <= 0).astype(float).where(f2.shares.notna())
    return leg1.fillna(0) + leg2.fillna(0) + leg3.fillna(0), f2

F2 = F.copy().sort_values(["symbol","fy"])
pio, F2 = pio_scores(F2)
F2["pio"] = pio
F2["avail"] = pd.to_datetime((F2.fy + 1).astype(str) + "-07-01")
dates_px = px.index
pio_sig = pd.DataFrame(np.nan, index=dates_px, columns=px.columns)
neg_eq = pd.DataFrame(np.nan, index=dates_px, columns=px.columns)
cols = {s: i for i, s in enumerate(px.columns)}
F2 = F2.sort_values(["symbol","avail"])
for _, r in F2.iterrows():
    j = cols.get(r.symbol)
    if j is None: continue
    m = dates_px >= r.avail
    pio_sig.iloc[np.where(m)[0], j] = r.pio
    ne = 1.0 if (pd.notna(r.equity) and r.equity < 0) else 0.0
    neg_eq.iloc[np.where(m)[0], j] = ne
pio_sig = pio_sig.where(px.notna()); neg_eq = neg_eq.where(px.notna())

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
            lw = pd.Series(1.0/nl, index=rs.index[-nl:])
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

idx = px.index
wk = idx.to_series().groupby([idx.isocalendar().year.values, idx.isocalendar().week.values]).max()
wk = [pd.Timestamp(d) for d in wk if d in idx]
rev5 = -rets_raw.rolling(5).sum()

def healthy(t, pmin):
    p = pio_sig.loc[t]
    ne = neg_eq.loc[t]
    ok = (p >= pmin) & (ne == 0)
    return ok.reindex(px.columns).fillna(False)

configs = [
    ("rev5 LS healthy(pio>=1)", lambda t: rev5.loc[t].where(healthy(t,1.0)), 1/3, 1/3, 2.0),
    ("rev5 LS healthy(pio>=2)", lambda t: rev5.loc[t].where(healthy(t,2.0)), 1/3, 1/3, 2.0),
    ("rev5 LS no-neg-eq", lambda t: rev5.loc[t].where((neg_eq.loc[t]==0).reindex(px.columns).fillna(False)), 1/3, 1/3, 2.0),
    ("rev5 LS healthy(pio>=2) 10d lag", lambda t: (rev5.loc[t]).where(healthy(t,2.0)), 1/3, 1/3, 2.0),
]
out = {}
for name, sf, lf, sfq, lev in configs:
    net, W, turn = build_rev(sf, wk, lf, sfq, lev)
    r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    mid = r.index[len(r)//2]
    sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
    sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
    negs = {int(k): round(v*100,1) for k,v in yr[yr<0].items()}
    print(f"{name:30s}: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} {negs} worst={yr.min():+.1%}")
    out[name] = r
pd.DataFrame(out).to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/rev_distress_raw.csv")
print("saved")
