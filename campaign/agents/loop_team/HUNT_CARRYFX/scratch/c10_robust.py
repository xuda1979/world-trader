"""Adversarial robustness of FINAL CFX4: parameter plateau, window sensitivity,
max single-day tail, turnover/cost drag, carry contribution split, FXMICRO-parity check."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
def build(books=B4,lbs=(21,63),carry=True,cap=2.0,div=2.0,start=None,end=None):
    nets=[]
    for (a,b) in books:
        zs=[zsig(C,a,b,lb,cap,div) for lb in lbs]
        W=sum(zs)/len(zs); sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST
        if carry:
            cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
            net=net+sig*cr.reindex(C.index).fillna(0.0)
        net=net-0.005/252*sig.abs()
        nets.append(net)
    out=pd.concat(nets,axis=1).mean(axis=1).dropna()
    if start: out=out[out.index>=start]
    if end: out=out[out.index<=end]
    return out
print("=== lb plateau (dual-tf pairs, carry=True) ===")
for lbs in [(10,21),(14,42),(21,63),(42,63),(21,42),(21,126),(63,126),(21,189)]:
    r=build(lbs=lbs); print(f"  lbs={lbs}: SR={sr(r):.3f} vol={r.std()*np.sqrt(252)*100:.2f}%")
print("=== single-tf fallback ===")
for lb in (21,42,63,126):
    r=build(lbs=(lb,)); print(f"  lb={lb}: SR={sr(r):.3f}")
print("=== window sensitivity (start cut) ===")
for s0 in ("2019-09-10","2020-01-01","2021-01-01","2022-01-01","2023-01-01"):
    r=build(start=s0); print(f"  {s0}+: n={len(r)} SR={sr(r):.3f}")
print("=== cap/div sensitivity ===")
for cap in (1.0,1.5,2.0,3.0):
    for div in (1.0,2.0):
        r=build(cap=cap,div=div); print(f"  cap={cap} div={div}: SR={sr(r):.3f}")
r=build()
x=r.abs().sort_values(ascending=False)
print(f"max |day| = {x.iloc[0]*100:.2f}% on {x.index[0].date()}; next4: {[f'{v*100:.2f}%@{d.date()}' for v,d in zip(x.iloc[1:5],x.index[1:5])]}")
# cost drag decomposition
g=0;t=0;ca=0
for (a,b) in B4:
    zs=[zsig(C,a,b,lb,2.0,2.0) for lb in (21,63)]
    W=sum(zs)/len(zs); sig=W.shift(1).reindex(r.index)
    g=g+ (sig*(R[a]-R[b]).reindex(r.index))
    t=t+ 2*sig.diff().abs()
    ca=ca+ sig*carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index).reindex(r.index).fillna(0.0)
gross=g/4; turn=t/4; carr=ca/4
print(f"ann gross={gross.mean()*252*100:.2f}%  cost={turn.mean()*COST*252*100:.2f}%  carry=+{carr.mean()*252*100:.2f}%  borrow=-{0.005*sig.abs().mean()*100:.3f}%  NET={r.mean()*252*100:.2f}%")
print(f"turnover one-side/day = {turn.mean()*100:.1f}% of book notional")
# no-carry vs carry SR on same window
print(f"no-carry SR={sr(build(carry=False)):.3f} vs carry SR={sr(build(carry=True)):.3f}")
