"""r6 shared helpers: general-rebalance-date backtester (T+1, 6bps), r6 charter gates,
circular-shift scramble (cost-inclusive), corr to CHAMPION_FINAL and to own saved sleeve.
Honesty: signal at t uses data <= t; weights effective t+1; costs 6bps x one-side turnover."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, vol_target, COST

px=D.closes(); RETS=px.pct_change(); IDX=RETS.index; NAMES=list(RETS.columns)
CH=pd.read_csv("/Users/daxu/software/world-trader/campaign/results/CHAMPION_FINAL_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
OLD=pd.read_csv("/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",index_col=0,parse_dates=True).iloc[:,0]
MES=[d for d in month_ends(RETS) if d in IDX]

def wback_rb(Wt, rets, rb_dates):
    """Target weights read at rb_dates (signal day t), effective t+1, hold to next rb.
    NOTE: a Wt row must exist for EVERY rb_date (zeros = flat); an rbd with no row
    holds stale positions (r6lib v1 bug, caught by r2lib cross-check 2007-12-03).
    Cost FULL |dw| x 6.4bps one-side charged at t+1 (TRADE_RECORD_STANDARD; CAMP_COST R2
    costfix 2026-09-07: was 0.5*|dw| x 6.0bps half-turn, an undercharge).
    Returns net series + daily weight df."""
    return wback_rb_core(Wt, rets, rb_dates, full_dw=True, bps=6.4)


def wback_rb_core(Wt, rets, rb_dates, full_dw=True, bps=6.4):
    """Parametrized core of wback_rb. full_dw=True, bps=6.4 = standard convention;
    full_dw=False, bps=6.0 reproduces the legacy half-turn (byte-recon only)."""
    idx=rets.index; T=len(idx); cols=list(rets.columns)
    vals=Wt.reindex(columns=cols)
    w=np.zeros((T,len(cols))); turn=np.zeros(T)
    rpos={d:i for i,d in enumerate(idx)}
    rd=sorted({rpos[d] for d in rb_dates if d in rpos})
    prev=np.zeros(len(cols)); curw=prev; rdi=0
    factor=1.0 if full_dw else 0.5
    for i in range(T):
        if rdi<len(rd) and rd[rdi]==i:
            neww=vals.loc[idx[i]].fillna(0.0).values
            if i+1<T:
                turn[i+1]=factor*np.abs(neww-prev).sum()
                curw=neww; prev=neww
            rdi+=1
        if i+1<T: w[i+1]=curw
    gross=(pd.DataFrame(w,index=idx,columns=cols)*rets.fillna(0.0)).sum(axis=1)
    net=gross-pd.Series(turn,index=idx)*bps/1e4
    return net, pd.DataFrame(w,index=idx,columns=cols)

def sret(net,start,target=0.10):
    r=net[net.index>=start]
    return vol_target(r,target=target).iloc[5:].dropna()

def gates6(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    mid=r.index[len(r)//2]; h1=r[r.index<=mid]; h2=r[r.index>mid]
    g=dict(SR=round(r.mean()/r.std()*np.sqrt(252),2),
        H1=round(h1.mean()/h1.std()*np.sqrt(252),2),H2=round(h2.mean()/h2.std()*np.sqrt(252),2),
        negYr=int((yr<0).sum()),worst=round(yr.min()*100,1),best=round(yr.max()*100,1),
        ann=round(r.mean()*252*100,1),vol=round(r.std()*np.sqrt(252)*100,1),
        maxdd=round(((1+r).cumprod()/(1+r).cumprod().cummax()-1).min()*100,1))
    g["ok6"]=(g["SR"]>=0.7 and g["H1"]>=0.35 and g["H2"]>=0.35 and g["negYr"]<=3 and g["worst"]>-8.0)
    g["ok_brief"]=(g["SR"]>=0.6 and g["H1"]>=0.3 and g["H2"]>=0.3 and g["negYr"]<=2 and g["worst"]>-5.0)
    return g

def xcorr(r,s):
    j=pd.concat([r.rename("a"),s.rename("b")],axis=1).dropna()
    return round(j.a.corr(j.b),3) if len(j)>100 else np.nan

def eval_rb(name,Wt,rbd,start,target=0.10,verbose=True):
    net,_=wback_rb(Wt,RETS,rbd)
    r=sret(net,start,target)
    g=gates6(r); g["corr_champ"]=xcorr(r,CH); g["corr_old"]=xcorr(r,OLD)
    if verbose: print(f"[{name}] vt={target}",g,flush=True)
    return r,g

def circ_scramble(builder,sig,start,target=0.10,nrep=200,seed=42,kmin=21,kmax=None,real_sr=None):
    """Circular time-shift of the SIGNAL PANEL rows (preserves xs structure+autocorr,
    breaks signal/return alignment). Rebuild weights via builder, reprice costs, same vt.
    Returns (p, null_sr_array): p = P(null SR >= real)."""
    vals=sig.values.copy(); T=sig.shape[0]
    kmax=kmax or T-1
    rng=np.random.default_rng(seed); srs=[]
    for _ in range(nrep):
        k=int(rng.integers(kmin,kmax+1))
        sp=pd.DataFrame(np.roll(vals,k,axis=0),index=sig.index,columns=sig.columns)
        Wt,rbd=builder(sp)
        net,_=wback_rb(Wt,RETS,rbd)
        rr=sret(net,start,target)
        srs.append(rr.mean()/rr.std()*np.sqrt(252))
    srs=np.array(srs)
    p=float((srs>=real_sr).mean())
    return p,srs

def ma_gate(win=200,band=0.03):
    ff=D.ff_factors(); mkt=(1+ff["Mkt-RF"]+ff["RF"]).cumprod()
    ma=mkt.rolling(win,min_periods=win).mean()
    g=pd.Series(np.where(mkt>ma*(1+band),1.0,np.where(mkt<ma*(1-band),0.0,np.nan)),index=mkt.index)
    return g.reindex(IDX).ffill().fillna(0.0)
