"""r6 Idea 3 — VOLUME-SHOCK REVERSAL event book: day t name drops >3% on volume >3x its
trailing 60d median volume (both known at t close) -> long at t+1, hold 5 days, equal weight,
max K names/day (biggest volume shock), overlap averaged. vt10 trailing expanding."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from r6lib import *

VOL=pd.DataFrame({k:v["vol"] for k,v in D.panel().items()})
VOL=VOL.reindex(columns=NAMES).sort_index()
VMED=VOL.rolling(60,min_periods=30).median().shift(1)   # trailing 60d median, excl today
VRATIO=VOL/VMED
DOWN=RETS<-0.03
SHOCK=DOWN&(VRATIO>3.0)
print("shock events total:",int(SHOCK.sum().sum()),"days w/ >=1:",int((SHOCK.sum(axis=1)>0).sum()),flush=True)

def event_ret(drop=0.03,vx=3.0,hold=5,kmax=5,start_min="2007-01-01"):
    ev=(RETS< -drop)&(VRATIO>vx)
    # rank by vratio, keep kmax per day
    r=VRATIO.where(ev)
    rbn=ev.sum(axis=1)
    W=pd.DataFrame(0.0,index=IDX,columns=NAMES)
    cnt=np.zeros(len(IDX))
    active=np.zeros(len(IDX))  # weight per name on each day
    rows=ev.values; vr=VRATIO.fillna(0.0).values
    T=len(IDX)
    for i in range(T):
        d=IDX[i]
        if d<pd.Timestamp(start_min): continue
        idxs=np.where(rows[i])[0]
        if len(idxs):
            vals=vr[i,idxs]
            order=np.argsort(-vals)[:kmax]
            picked=idxs[order]
            # enter at i+1..i+hold equal split 1/(kmax*?) weight = 1/kmax each? cap NAV 1: w=1/kmax
            for j in picked:
                for h in range(1,hold+1):
                    if i+h<T: cnt[i+h]+=1
        # weights matrix add later
    Wd=pd.DataFrame(0.0,index=IDX,columns=NAMES)
    rows2=ev.values
    for i in range(T):
        d=IDX[i]
        if d<pd.Timestamp(start_min): continue
        idxs=np.where(rows2[i])[0]
        if len(idxs):
            vals=vr[i,idxs]
            order=np.argsort(-vals)[:kmax]
            picked=idxs[order]
            for h in range(1,hold+1):
                if i+h<T:
                    j=i+h
                    for s in picked:
                        Wd.iloc[j,s]+=1.0/max(kmax,1)
    # normalize days where total>1 (overlap): scale to <=1 NAV
    tot=Wd.abs().sum(axis=1)
    scale=(1.0/tot).clip(upper=1.0).fillna(0.0)
    Wd=Wd.mul(scale,axis=0)
    return Wd

for drop,vx,hold,kmax in [(0.03,3.0,5,5),(0.03,3.0,5,10),(0.05,3.0,5,5),(0.03,2.0,5,5),(0.03,3.0,10,5)]:
    Wd=event_ret(drop,vx,hold,kmax)
    Wt=Wd.copy()
    # event books trade at t+1 already by construction (weights start i+1); rbd=days where Wt changes
    diff=Wt.diff().abs().sum(axis=1).fillna(0.0)
    rbd=list(IDX[(diff>0)|(diff.shift(-1).fillna(0)>0)])
    net,_=wback_rb(Wt,RETS,rbd)
    nz=Wt.abs().sum(axis=1); start=nz[nz>0].index[0]
    r=sret(net,start,0.10)
    g=gates6(r); g["corr_champ"]=xcorr(r,CH); g["corr_old"]=xcorr(r,OLD)
    print(f"drop{drop} vx{vx} hold{hold} k{kmax} events={int(SHOCK.sum().sum())}",{k:g[k] for k in['SR','H1','H2','negYr','worst','ann','corr_champ','corr_old','ok6']},flush=True)
