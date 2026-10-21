#!/usr/bin/env python3
"""Match claimed headlines (43.8% ann, SR_d 3.91, SR_m 3.99, -4.96% DD, worst-3y -4.96%,
0/19, OOS17arith 40.8%) to exact conventions on the committed V2 BAL file."""
import numpy as np, pandas as pd
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]

def rep(r, tag):
    r = r.dropna()
    srd = r.mean()/r.std()*np.sqrt(252)
    m = (1+r).resample('ME').prod()-1
    srm_ms = m.mean()/m.std()*np.sqrt(12)
    # alt SR_m: mean/std of monthly simple sums
    mm = r.groupby(r.index.to_period('M')).sum()
    srm_ms2 = mm.mean()/mm.std()*np.sqrt(12)
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()
    n = len(r)
    ann_geo = eq.iloc[-1]**(252/n)-1
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    o = r[r.index >= '2017-01-01']
    print(f"{tag}: n={n} span {r.index[0].date()}..{r.index[-1].date()}")
    print(f"  ann_geo {ann_geo*100:.2f} | SR_d {srd:.3f} | SR_m(me) {srm_ms:.3f} | SR_m(sum) {srm_ms2:.3f} | MDD {mdd*100:.2f}")
    print(f"  neg {int((yr<0).sum())}/{yr.size} | OOS17 arith {o.mean()*252*100:.2f}")
    return r

rep(v2, "full span")
r08 = v2[(v2.index >= '2008-03-31') & (v2.index <= '2026-07-31')]
rep(r08, "2008-03-31..2026-07-31")
r08b = v2[v2.index >= '2008-01-01']
rep(r08b, "2008-01-01..end")
r07 = v2[(v2.index >= '2008-03-31')]
rep(r07, "2008-03-31..end")
# DD episode of the -4.96%: dates and length
r = v2.dropna(); eq = (1+r).cumprod()
roll = eq.cummax(); dd = eq/roll-1
itr = dd.idxmin()
peak = eq[:itr].idxmax()
rec = dd[itr:][dd[itr:] > -1e-12]
recd = rec.index[0] if len(rec) else None
print(f"\nMaxDD {dd.min()*100:.2f}% trough {itr.date()}, peak {peak.date()}, recovered {recd.date() if recd is not None else 'NEVER'}, episode {(recd-peak).days if recd is not None else -1} cal days")
# worst 3y: max drawdown within each rolling 756d window (peak-to-trough inside window)
w = 756
worst = 0; wd = None
vals = eq.values
n = len(vals)
import numpy as np
for i in range(n-w):
    seg = vals[i:i+w+1]
    mdd_w = (seg/np.maximum.accumulate(seg)-1).min()
    if mdd_w < worst: worst, wd = mdd_w, eq.index[i]
print(f"worst within-756d-window MaxDD: {worst*100:.2f}% (window start {wd.date() if wd is not None else '-'})")
