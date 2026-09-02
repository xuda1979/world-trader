#!/usr/bin/env python3
"""The claim 'worst-3y -4.96%' — that matches DD-window reading, but check MaxDD-window LENGTH:
the -4.96% DD trough 2011-02-14 peak 2011-01-03 is a 6-week episode. Which interpretation gives
-4.96%? Also audit SAFE and AGGR claims (SAFE MaxDD -4.96% too?). And compute the OOS17 of both."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
for v in ["SAFE", "BALANCED", "AGGRESSIVE"]:
    r = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_{v}_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    r08 = r[(r.index >= '2008-03-31')]
    eq = (1+r08).cumprod()
    dd = eq/eq.cummax()-1
    vals = eq.values
    worst = 0; wi = None
    for i in range(len(vals)-756):
        seg = vals[i:i+757]
        d = (seg/np.maximum.accumulate(seg)-1).min()
        if d < worst: worst, wi = d, eq.index[i]
    m = (1+r08).resample('ME').prod()-1
    o = r08[r08.index >= '2017-01-01']
    print(f"{v}: MDD {dd.min()*100:.2f}% | worst-756d-DD {worst*100:.2f}% (from {wi.date()}) | OOS17 arith {o.mean()*252*100:.2f}% | SR_m {m.mean()/m.std()*np.sqrt(12):.3f}")
