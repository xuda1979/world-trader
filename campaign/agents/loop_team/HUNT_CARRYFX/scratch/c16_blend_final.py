import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/VET_HONESTY/audit")
import numpy as np, pandas as pd
import gate_harness as gh
ROOT="/Users/daxu/software/world-trader"
l16=gh.readv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv").dropna()
cf=pd.read_csv("sleeves/CFX4_DTF21_63_raw_daily.csv",index_col=0,parse_dates=True)["ret"]
rc=cf.reindex(l16.index).fillna(0.0)
s=rc.rolling(60,min_periods=60).std().shift(1)*np.sqrt(252)
cfx=(rc*(0.05/s).clip(upper=3.0).fillna(0.0))
def srm(r):
    m=(1+r).resample('ME').prod()-1; return float(m.mean()/m.std()*np.sqrt(12))
def srd(r): return float(r.mean()/r.std()*np.sqrt(252))
def geo(r): return float((1+r).prod()**(252/len(r))-1)*100
for w in (0.0,0.02,0.05,0.10,0.15,0.20):
    bl=l16*(1-w)+cfx*w
    yr=bl.groupby(bl.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"w={w:.2f}: SR_d={srd(bl):.3f} SR_m={srm(bl):.3f} ann_geo={geo(bl):.2f}% negyrs={int((yr<0).sum())}")
