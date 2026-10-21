"""Backtest the best IC leg: s_ta (asset turnover, annual) Q-LS 33/33 lev2, Q3 hygiene."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, month_ends)
import numpy as np, pandas as pd

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)

f = F.copy().sort_values(["symbol","fy"])
f["s_ta"] = f.revenue / f.total_assets.where(lambda s: s>0)
f["z"] = f.groupby("fy")["s_ta"].transform(lambda s: (s-s.median())/s.std()).clip(-3,3)
f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
dates = px.index
sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
cols = {s: i for i, s in enumerate(px.columns)}
f = f.sort_values(["symbol","avail"])
for _, r in f.iterrows():
    j = cols.get(r.symbol)
    if j is None or pd.isna(r["z"]): continue
    m = dates >= r.avail
    sig.iloc[np.where(m)[0], j] = r["z"]
sig = sig.where(px.notna())

def build(dates_rb, lf, sf, lev):
    idx = px.index
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(dates_rb):
        row = sig.loc[t].dropna()
        row = row[~bad_tr.loc[t].astype(bool).reindex(row.index).fillna(False)]
        if len(row) < 10:
            neww = pd.Series(0.0, index=px.columns)
        else:
            rs = row.sort_values(); n = len(rs)
            nl = max(int(np.floor(n*lf)),1); ns = max(int(np.floor(n*sf)),1)
            lw = pd.Series(1.0/nl, index=rs.index[-nl:]); sw = pd.Series(1.0/ns, index=rs.index[:ns])
            neww = lw.subtract(sw, fill_value=0.0).reindex(px.columns).fillna(0.0)*lev/2.0
        nxt = dates_rb[k+1] if k+1<len(dates_rb) else idx[-1]
        i0 = idx.get_loc(t)+1
        if i0>=len(idx): break
        W.iloc[i0:min(idx.get_loc(nxt)+1,len(idx))] = neww.values[None,:]
        turn.iloc[i0] = 0.5*(neww-prev).abs().sum(); prev=neww
    gross = (W*rets_w.fillna(0.0)).sum(axis=1)
    sn = -(W.clip(upper=0.0)).sum(axis=1)
    net = gross - turn*COST_BPS/1e4 - sn*BORROW/252
    return net, W

mes = [pd.Timestamp(d) for d in month_ends(px.index)]
net, W = build(mes, 1/3, 1/3, 2.0)
r = vol_target(net).iloc[5:].dropna(); r = r[r.index>='2009-07-01']
yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
sr = r.mean()/r.std()*np.sqrt(252)
mid = r.index[len(r)//2]
sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
negs = {int(k): round(v*100,1) for k,v in yr[yr<0].items()}
print(f"s_ta Q-M LS 33/33 lev2: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} {negs} MDD={((1+r).cumprod()/(1+r).cumprod().cummax()-1).min():+.1%}")
# long leg only
netL, WL = build(mes, 1.0, 0.0, 1.0)
rL = vol_target(netL).iloc[5:].dropna(); rL = rL[rL.index>='2009-07-01']
print(f"s_ta long-only top tercile: SR={rL.mean()/rL.std()*np.sqrt(252):+.2f} ann={(1+rL).prod()**(252/len(rL))-1:+.1%}")
