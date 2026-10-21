"""Reconcile claimed 3.45x mean / p95 7.18x; recompute corr FF2<->V3/V2; V2+HONEST11 at 1.6x; FF2 gap days."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V3/scratch")
from a_rebuild import load, POOL, NEW3, NEW2, make, build, stats

Sd,capW,blend,tw,wts=make(NEW3)
A,fullA,gbA,scA,_,_,_=build(capW,blend,tw,0.07,0.04)
B,fullB,gbB,scB,_,_,_=build(capW,blend,tw,0.091,0.03)
BAL=((A+B)/2).dropna()
def gl(full,sc,idx):
    g=full.fillna(0).abs().sum(axis=1)
    return g.reindex(idx).fillna(0)
idx=BAL.index
variants={
 "BAL mean(A,B), thr in, 2008+":        ((gl(fullA,scA,idx)+gl(fullB,scB,idx))/2)[idx>='2008-03-31'],
 "BAL, throttle OFF, 2008+":            ((capW.mul(gbA,axis=0)+capW.mul(gbB,axis=0))/2).abs().sum(axis=1).reindex(idx).fillna(0)[idx>='2008-03-31'],
 "BAL full window 2006-10+":            ((gl(fullA,scA,idx)+gl(fullB,scB,idx))/2),
 "SAFE 2008+":                           gl(fullA,scA,idx)[idx>='2008-03-31'],
 "AGGR 2008+":                           gl(fullB,scB,idx)[idx>='2008-03-31'],
}
for k,v in variants.items():
    print(f"lev[{k}]: mean {v.mean():.3f}x p50 {v.median():.3f}x p95 {np.percentile(v,95):.3f}x max {v.max():.3f}x")

print("\n=== corr FF2 to V3 BAL (delivered claim was vs V2 BAL) ===")
ff2=load("campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv").dropna()
for tgt in ["GOAL100_HONEST14V3_BALANCED_daily.csv","GOAL100_HONEST13V2_BALANCED_daily.csv"]:
    c=load(f"campaign/results/{tgt}")
    j=pd.concat([ff2.rename('f'),c.rename('c')],axis=1,join='inner').dropna()
    print(f"corr(FF2, {tgt.split('_')[1]}): {j.f.corr(j.c):+.4f} n={len(j)}")

print("\n=== FF2 gap: champion days after 2026-06-30 ===")
gap=BAL[BAL.index>'2026-06-30']
print(f"n gap days={len(gap)} span {gap.index[0].date()}..{gap.index[-1].date()} V3 cum ret on gap {(1+gap).prod()-1:+.3%}")
ff2_raw_mean=ff2[ff2.index>='2008-01-01'].mean()
print(f"FF2 long-run mean/day 2008+ {ff2_raw_mean*1e4:.2f}bps; 42d hypothetical (mean) {ff2_raw_mean*len(gap)*100:+.2f}% (UNVERIFIED — data absent)")

print("\n=== V2 BAL (13eng) at real 1.6x ===")
Sd2,capW2,blend2,tw2,wts2=make(NEW2)
A2,fullA2,_,_,_,_,_=build(capW2,blend2,tw2,0.07,0.04)
B2,fullB2,_,_,_,_,_=build(capW2,blend2,tw2,0.091,0.03)
BAL2=((A2+B2)/2).dropna()
g2=((fullA2.fillna(0).abs().sum(axis=1)+fullB2.fillna(0).abs().sum(axis=1))/2).reindex(BAL2.index).fillna(0)
live2=g2[g2.index>='2008-03-31']
print(f"V2 gross: mean {live2.mean():.3f}x p95 {np.percentile(live2,95):.3f}x max {live2.max():.3f}x")
f2=(1.6/live2).clip(upper=1.0)
fin2=(live2*f2-1).clip(lower=0)*0.045/252
r16_2=(BAL2*f2-fin2.reindex(BAL2.index).fillna(0)).dropna()
stats(r16_2,"V2 BAL @1.6x + 4.5% margin")
f2b=(1.6/live2).clip(upper=1.0)
r16_2b=(BAL2*f2b).dropna()
stats(r16_2b,"V2 BAL @1.6x no margin")
