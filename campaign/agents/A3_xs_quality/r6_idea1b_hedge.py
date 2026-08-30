"""r6 Idea 1b — beta-hedged weekday momentum: long top-weekday-quintile names,
plus hedge leg -1 x FF-market short (beta-hedge 1.0) held on same rebalance days.
Hedge return stream = FF Mkt-RF+RF daily; hedge turnover cost charged on the rebalance
days only (weekly, tiny). This kills the equity-beta corr while keeping the xs tilt."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from r6lib import *
from r6_idea1_weekdaymom import S, start_scores, ff, build

mkt=(ff["Mkt-RF"]+ff["RF"]).reindex(IDX).fillna(0.0)

for frac,beta in [(0.2,1.0),(0.3,1.0),(0.2,0.8),(0.2,1.2),(0.3,1.2)]:
    Wt,rbd=build(S,frac=frac,mode="LO")
    net,_=wback_rb(Wt,RETS,rbd)
    inv=(Wt.abs().sum(axis=1)>0)
    mh=mkt.copy()
    turn=pd.Series(0.0,index=IDX); state=0.0
    Hw=pd.Series(0.0,index=IDX)
    for d in rbd:
        i=IDX.get_loc(d)
        if i+1<len(IDX):
            Hw.iloc[i+1:]= -beta if inv.loc[d] else 0.0
    gross=net+Hw*mkt
    # hedge turnover: change in Hw
    th=Hw.diff().abs().fillna(0.0)
    comb=gross-th*COST/1e4
    r=sret(comb,start_scores,0.10)
    g=gates6(r); g["corr_champ"]=xcorr(r,CH); g["corr_old"]=xcorr(r,OLD)
    print(f"hedged wd LO frac={frac} beta={beta}",{k:g[k] for k in['SR','H1','H2','negYr','worst','ann','corr_champ','corr_old','ok6']},flush=True)
