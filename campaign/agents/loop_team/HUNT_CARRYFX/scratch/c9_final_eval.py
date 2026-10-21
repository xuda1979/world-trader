"""FINAL: raw (un-vt'd) CFX4 composite — 4 books x dual-tf z(21,63) + PIT carry accrual,
borrow 0.5%/yr, 6bps/side. Full gate battery + VET harness + marginal value vs champion."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/VET_HONESTY/audit")
import numpy as np, pandas as pd, json
from cfx_lib import *
import gate_harness as gh
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]

def build_final(books=B4,lbs=(21,63),carry=True):
    nets=[]
    for (a,b) in books:
        zs=[zsig(C,a,b,lb,2.0,2.0) for lb in lbs]
        W=sum(zs)/len(zs); sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST
        if carry:
            cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
            net=net+sig*cr.reindex(C.index).fillna(0.0)
        net=net-0.005/252*sig.abs()
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()

raw=build_final()
raw.to_csv("sleeves/CFX4_DTF21_63_carry_raw_daily.csv",header=["ret"])
st=stats(raw)
print("FINAL CFX4 raw:",json.dumps(st))
yr=raw.groupby(raw.index.year).apply(lambda x:(1+x).prod()-1)
print("yearly:",{int(k):round(v*100,2) for k,v in yr.items()})
print("scrub:",{k:round(scrub_sr(raw,k),3) for k in (5,10,20,50)})
x=raw.dropna().values; n=len(x); srs=[]
for s0 in range(0,n-63,63):
    keep=np.ones(n,bool); keep[s0:s0+63]=False
    srs.append(sr(pd.Series(x[keep],index=raw.dropna().index[keep])))
print(f"epjackMin={min(srs):.2f} (of {len(srs)} windows)  LOYO={min(sr(raw[raw.index.year!=y]) for y in range(2020,2027)):.2f}")
print(f"block-boot pA(1k,seed0)={block_boot_p(raw,10,1000,0):.4f}")
# VET permanent harness (note: it trims to 2008-09+; n08 = full here)
v=gh.vet("sleeves/CFX4_DTF21_63_carry_raw_daily.csv")
print("VET harness:",json.dumps({k:v[k] for k in ("n08","verdict","fails","flatten","perf","corr")},default=str))
# T+1 probe detail
t1=gh.t1_gate(raw)
print("T+1 probe:",json.dumps(t1))
# correlations to champion files
for tag,p in [("H11_BAL",f"{ROOT}/campaign/results/GOAL100_HONEST11_daily_BALANCED_daily.csv"),
              ("HONEST11FIX_BAL",f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv"),
              ("HONEST11L16_BAL",f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv")]:
    h=gh.readv(p).dropna()
    j=pd.concat([raw.rename("c"),h.rename("h")],axis=1,join="inner").dropna()
    print(f"corr vs {tag}: {j.corr().iloc[0,1]:+.4f} (n={len(j)})")
# marginal value: add vt5-scaled CFX4 to HONEST11-L16 BALANCED
l16=gh.readv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv").dropna()
rc=raw.reindex(l16.index).fillna(0.0)
s=rc.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
scale=(0.05/s).clip(upper=3.0).fillna(0.0)   # 5% vol slice, T+1 trailing; 0 until 60d history
cfx_vt=(rc*scale)
print(f"\nCFX4 vt5-slice: SR={sr(cfx_vt[cfx_vt!=0]):.3f} vol={cfx_vt[cfx_vt!=0].std()*np.sqrt(252)*100:.2f}%")
base_m=(1+l16).resample('ME').prod()-1
print(f"champion alone: SR_d={sr(l16):.3f} SR_m={sr(base_m):.3f} ann_geo={((1+l16).prod()**(252/len(l16))-1)*100:.2f}%")
for w in (0.02,0.05,0.10,0.15):
    bl=l16*(1-w)+cfx_vt*w
    bm=(1+bl).resample('ME').prod()-1
    yrr=bl.groupby(bl.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"  w={w:.2f}: SR_d={sr(bl):.3f} SR_m={sr(bm):.3f} ann_geo={((1+bl).prod()**(252/len(bl))-1)*100:.2f}% negyrs={int((yrr<0).sum())}")
