"""Momentum on LIQUID subpanel ONLY (twelve_big, no OTC) with Q3 hygiene — kills the
'microstructure garbage drives it' objection AND stays pipeline-compatible with dualmom."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
from run_ideas2_lib import (px, F, sigv, sigp, month_ends)
import numpy as np, pandas as pd, os

d1 = "/Users/daxu/software/world-trader/tools/quant/data/twelve_big"
big = set(fn[:-4] for fn in os.listdir(d1) if fn.endswith('.csv'))

rets_raw = px.pct_change(fill_method=None)
rets_w = rets_raw.clip(-0.5, 0.5)
bad25 = (rets_raw.abs() > 0.25)
bad_tr = bad25.rolling(504, min_periods=1).max().shift(1).fillna(0.0)
idx = px.index
mes = [pd.Timestamp(d) for d in month_ends(idx)]

def build(topfrac, cheap, use_liquid):
    W = pd.DataFrame(0.0, index=idx, columns=px.columns)
    turn = pd.Series(0.0, index=idx); prev = pd.Series(0.0, index=px.columns)
    for k, t in enumerate(mes):
        m = ((px.shift(21)/px.shift(252)-1).loc[t]).clip(-0.95, 3.0)
        if use_liquid:
            m = m.where(m.index.isin(big))
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

for liq, cheap, frac in [(True, False, 1/3), (True, True, 1/3), (True, True, 1/2), (True, False, 1/2)]:
    r = build(frac, cheap, liq)
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    sr = r.mean()/r.std()*np.sqrt(252)
    mid = r.index[len(r)//2]
    sr1 = r[r.index<=mid].mean()/r[r.index<=mid].std()*np.sqrt(252)
    sr2 = r[r.index>mid].mean()/r[r.index>mid].std()*np.sqrt(252)
    negs = {int(k): round(v*100,1) for k,v in yr[yr<0].items()}
    print(f"liquid={liq} cheap={cheap} frac={frac:.2f}: SR={sr:+.2f} H1={sr1:+.2f} H2={sr2:+.2f} ann={(1+r).prod()**(252/len(r))-1:+.1%} negy={int((yr<0).sum())} {negs}")
# save best: liquid, cheap, 1/2  => final candidate v2
r = build(0.5, True, True)
r.to_frame("ret").to_csv("/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch/HF_mom_cheap_liq_daily.csv")
print("saved HF_mom_cheap_liq_daily.csv n=", len(r))
