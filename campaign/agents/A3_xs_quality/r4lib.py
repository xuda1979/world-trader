"""r4 shared helpers: weights builder + gated backtest + corrected vol-target
(trim to active window FIRST, r1 lesson) + full r4 gate battery."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, vol_target, COST
from r2lib import wbacktest

px=D.closes(); RETS=px.pct_change(); IDX=RETS.index
MES=[d for d in month_ends(RETS) if d in px.index]
CH=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv",index_col=0,parse_dates=True).iloc[:,0]

def ma_gate(win=200,band=0.03):
    ff=D.ff_factors(); mkt=(1+ff["Mkt-RF"]+ff["RF"]).cumprod()
    ma=mkt.rolling(win,min_periods=win).mean()
    g=pd.Series(np.where(mkt>ma*(1+band),1.0,np.where(mkt<ma*(1-band),0.0,np.nan)),index=mkt.index)
    return g.reindex(IDX).ffill().fillna(0.0)

def long_top(scores,frac,gate=None,floor=10):
    """Long-only top-frac equal weight at month-ends, optional gate series (flat when <=0)."""
    W=pd.DataFrame(0.0,index=IDX,columns=px.columns)
    for t in MES:
        if t not in scores.index: continue
        if gate is not None and gate.loc[t]<=0: continue
        row=scores.loc[t].dropna()
        if len(row)<floor: continue
        row=row.sort_values(); nl=max(int(np.floor(len(row)*frac)),1)
        for s in row.index[-nl:]: W.loc[t,s]=1.0/nl
    return W

def sret(net,target,start):
    r=net[net.index>=start]
    return vol_target(r,target=target).iloc[5:].dropna()

def gates(r,full=True):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    mid=r.index[len(r)//2]; h1=r[r.index<=mid]; h2=r[r.index>mid]
    g=dict(SR=round(r.mean()/r.std()*np.sqrt(252),2),H1=round(h1.mean()/h1.std()*np.sqrt(252),2),
        H2=round(h2.mean()/h2.std()*np.sqrt(252),2),negYr=int((yr<0).sum()),worst=round(yr.min()*100,1),
        ann=round(r.mean()*252*100,1),vol=round(r.std()*np.sqrt(252)*100,1),
        maxdd=round(((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()*100,1))
    if full:
        g["ok_std"]=g["SR"]>=0.6 and g["H1"]>=0.3 and g["H2"]>=0.3 and g["negYr"]<=2 and g["worst"]>-5.0
        g["ok_r4"]=g["SR"]>=0.6 and g["H1"]>=0.4 and g["H2"]>=0.4 and g["negYr"]<=2 and g["worst"]>-5.0
    return g

def corr_champ(r):
    j=pd.concat([r.rename("a"),CH.rename("c")],axis=1).dropna()
    return j.a.corr(j.c)

def scramble(W_of_scores,scores,gate,target,start,nrep=200,seed=42):
    """xs-permute scores, rebuild weights, cost-inclusive nulls at same vt."""
    vals=scores.values.copy(); mask=~np.isnan(vals); v=vals[mask]
    rng=np.random.default_rng(seed); srs=[]
    for _ in range(nrep):
        pv=v.copy(); rng.shuffle(pv); p2=np.full_like(vals,np.nan); p2[mask]=pv
        sp=pd.DataFrame(p2,index=scores.index,columns=scores.columns)
        net,_,_=wbacktest(W_of_scores(sp),RETS)
        rr=sret(net,target,start)
        srs.append(rr.mean()/rr.std()*np.sqrt(252))
    return np.array(srs)

def evaluate(name,W,target,verbose=True):
    net,_,_=wbacktest(W,RETS)
    nz=W.abs().sum(axis=1); start=nz[nz>0].index[0]
    if start is None: print(name,"never invested"); return None
    r=sret(net,target,start)
    g=gates(r)
    g["corr_champ"]=round(corr_champ(r),3)
    if verbose:
        print(f"[{name}] vt={target} {g}")
    return dict(r=r,g=g,start=start,net=net)
