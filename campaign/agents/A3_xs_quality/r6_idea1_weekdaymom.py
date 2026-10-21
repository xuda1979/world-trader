"""r6 Idea 1 — DAILY SEASONAL MOMENTUM: trailing-2y same-weekday mean excess return.
Signal_t for name i = mean over trailing 504 trading days of (ret_{i, same weekday} - mkt).
Weekly rebalance (first trading day of ISO week). Long top quintile (weekday profile).
Long-only top-Q + market-neutral-hedge variants. T+1, 6bps, vt10 trailing expanding."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from r6lib import *

RETS_F=RETS.fillna(0.0)
wd=RETS.index.weekday
ff=D.ff_factors(); mkt=ff["Mkt-RF"]+ff["RF"]
X=RETS.sub(mkt.reindex(RETS.index).fillna(0.0),axis=0)   # excess over market (daily)

def weekday_score(LB=504):
    """Score matrix at every trading day: mean same-weekday excess return over trailing LB."""
    S=pd.DataFrame(np.nan,index=IDX,columns=NAMES)
    Xv=X.values
    for t in range(LB,len(IDX)):
        d0=IDX[t]; k=int(wd[t])
        rows=np.arange(t-LB,t)
        sel=rows[wd[rows]==k]
        S.loc[d0]=np.nanmean(Xv[sel],axis=0)
    return S

def build(sig,frac=0.2,mode="LO",weekly=True,min_names=30):
    """Weekly (Mon) rebalance; mode LO=long top frac; LS=long top / short bottom frac."""
    rbd=[]; Wt=pd.DataFrame(0.0,index=IDX,columns=NAMES)
    used=set()
    for t in range(len(IDX)):
        d=IDX[t]
        if weekly and d.weekday()!=0: continue
        if d not in sig.index: continue
        row=sig.loc[d].dropna()
        if len(row)<min_names: continue
        row=row.sort_values(); n=len(row)
        nl=max(int(np.floor(n*frac)),1)
        w=pd.Series(0.0,index=NAMES)
        if mode=="LS":
            ns=max(int(np.floor(n*frac)),1)
            for s in row.index[-nl:]: w[s]=1.0/nl
            for s in row.index[:ns]: w[s]-=1.0/ns
        else:
            for s in row.index[-nl:]: w[s]=1.0/nl
        Wt.loc[d]=w.values; rbd.append(d); used.add(d)
    return Wt,rbd

# monthly scores snapshot at Monday rebalances only (compute lazily: score once per week)
LB=504
S=weekday_score(LB)
start_scores=S.dropna(how="all").index[0]
print("scores start:",start_scores,flush=True)

res={}
for mode,frac in [("LO",0.2),("LO",0.3),("LS",1/3)]:
    Wt,rbd=build(S,frac=frac,mode=mode)
    r,g=eval_rb(f"wd{LB}_{mode}_{frac:.2f}",Wt,rbd,start=start_scores)
    res[(mode,frac)]=(r,g)
