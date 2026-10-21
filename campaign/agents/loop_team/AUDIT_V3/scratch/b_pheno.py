"""AUDIT_V3 target 6: phenomenology sweep — ac1 / distinct-value red-flags on ALL 14 V3 sleeves
(as builder ingests them: pool via holiday rollup, new via dropna) + V3 blend itself."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V3/scratch")
from a_rebuild import load, rollup, POOL, NEW3, make, build
rows=[]
for n,p in POOL.items(): rows.append((n,p,rollup(load(p))))
for n,p in NEW3.items(): rows.append((n,p,load(p).dropna()))
print(f"{'sleeve':10s} {'n':>6s} {'start':>11s} {'end':>11s} {'ac1':>7s} {'uniqR':>7s} {'nuniq':>7s} {'zerofrac':>8s} FLAG")
for n,p,r in rows:
    ac1=float(r.autocorr(1)); uq=r.round(10).nunique(); ur=uq/len(r); zf=(r==0).mean()
    flag=[]
    if ac1>0.5: flag.append("AC1>0.5")
    if ur<0.08: flag.append("UNIQ<8%")
    print(f"{n:10s} {len(r):6d} {str(r.index[0].date()):>11s} {str(r.index[-1].date()):>11s} {ac1:7.3f} {ur:7.3f} {uq:7d} {zf:8.3f} {','.join(flag) or '-'}")
Sd,capW,blend,tw,wts=make(NEW3)
A,_,_,_,_,_,_=build(capW,blend,tw,0.07,0.04); B,_,_,_,_,_,_=build(capW,blend,tw,0.091,0.03)
BAL=((A+B)/2).dropna()
ac1=float(BAL.autocorr(1)); ur=BAL.round(10).nunique()/len(BAL)
print(f"{'V3_BAL':10s} {len(BAL):6d} {'':11s} {'':11s} {ac1:7.3f} {ur:7.3f} {BAL.round(10).nunique():7d} {(BAL==0).mean():8.3f} {'AC1>0.5' if ac1>0.5 else ''}{' UNIQ<8%' if ur<0.08 else ''}")
