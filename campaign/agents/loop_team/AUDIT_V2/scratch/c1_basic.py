#!/usr/bin/env python3
"""AUDIT_V2 check 1: committed V2 file basic structure + BAL==(SAFE+AGGR)/2 + headline stats."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
R = f"{ROOT}/campaign/results"

def load(fn):
    df = pd.read_csv(f"{R}/{fn}", index_col=0, parse_dates=True)
    return df.iloc[:, 0].astype(float)

def stats(r, name):
    r = r.dropna()
    eq = (1+r).cumprod()
    mdd = (eq/eq.cummax()-1).min()
    srd = r.mean()/r.std()*np.sqrt(252)
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12)
    ann_geo = eq.iloc[-1]**(252/len(r))-1
    ann_arith = r.mean()*252
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    o = r[r.index >= '2017-01-01']
    oos_arith = o.mean()*252
    oos_geo = (1+o).prod()**(252/len(o))-1
    print(f"{name}: n={len(r)} span {r.index[0].date()}..{r.index[-1].date()}")
    print(f"  ann_geo {ann_geo*100:.2f}%  ann_arith {ann_arith*100:.2f}%  SR_d {srd:.3f}  SR_m {srm:.3f}  MaxDD {mdd*100:.2f}%")
    print(f"  neg yrs {int((yr<0).sum())}/{yr.size} worst {yr.min()*100:.2f}% best {yr.max()*100:.2f}%  OOS17 arith {oos_arith*100:.2f}% geo {oos_geo*100:.2f}%")
    # worst 3y subwindow (756 trading days)
    w = (1+r).cumprod()
    r3 = w/w.shift(756)-1
    i3 = r3.idxmin()
    print(f"  worst 756d-trading-day window: {r3.min()*100:.2f}% ending {i3.date()}")
    # calendar-3y windows too
    yr3 = []
    ys = sorted(set(r.index.year))
    for y0 in range(ys[0], ys[-1]-1):
        rr = r[(r.index.year>=y0)&(r.index.year<=y0+2)]
        if len(rr)>500: yr3.append(((1+rr).prod()-1, y0))
    yr3.sort()
    print(f"  worst calendar-3y window: {yr3[0][0]*100:.2f}% ({yr3[0][1]}-{yr3[0][1]+2})")
    return r

safe = load("GOAL100_HONEST13V2_SAFE_daily.csv")
bal  = load("GOAL100_HONEST13V2_BALANCED_daily.csv")
aggr = load("GOAL100_HONEST13V2_AGGRESSIVE_daily.csv")
half = ((safe+aggr)/2).dropna()
j = pd.concat([bal.rename('bal'), half.rename('half')], axis=1, join='outer')
both = j.dropna()
print(f"BAL rows {len(bal)}, (SAFE+AGGR)/2 rows {len(half)}, overlap {len(both)}")
print(f"index-only BAL: {len(bal)-len(both)}, index-only HALF: {len(half)-len(both)}")
print(f"max|BAL-(SAFE+AGGR)/2| on overlap = {float((both.bal-both.half).abs().max()):.3e}")
print()
stats(safe, "SAFE"); print(); stats(bal, "BALANCED"); print(); stats(aggr, "AGGRESSIVE")
# scoped stats 2008+
print("\n--- scoped 2008-03-31..2026-07-31 (comparable span) ---")
for nm, r in [("SAFE", safe), ("BAL", bal), ("AGGR", aggr)]:
    rs = r[(r.index>='2008-03-31')&(r.index<='2026-07-31')]
    stats(rs, nm+" [08-]")
