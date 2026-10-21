"""Avellaneda-Lee proper: OU half-life screening + stateful positions, honest.
For each stock, rolling 60d: residual e_t; fit AR(1) e_t = a + b e_{t-1}; half-life = -ln2/ln(b).
Only trade names with 2<HL<60d (mean-reverting). s-score = (e-mu)/sd. Enter |s|>1.25, exit |s|<0.75.
Market-neutral book (net ~0). P&L on residual returns, T+1, 5bp one-way. Test BOTH reversion signs.
"""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CLASSIC_SPREADS/scratch')
import engine as E
champ=E.champ_ref()

def markov_zscores(resid, lookback=60):
    """Return per-stock s-scores that ONLY trade mean-reverting (half-life bounded) names, else 0."""
    out=pd.DataFrame(0.0,index=resid.index,columns=resid.columns)
    hl=pd.DataFrame(np.nan,index=resid.index,columns=resid.columns)
    rv=resid.values; T,N=rv.shape
    # precompute rolling mean/sd
    for c in range(N):
        r=pd.Series(rv[:,c],index=resid.index)
        mu=r.rolling(lookback,min_periods=lookback).mean()
        sd=r.rolling(lookback,min_periods=lookback).std()
        z=(r-mu)/sd
        out.iloc[:,c]=z.values
        # rolling AR(1) b via cov/lag var on window
        x=r.values
        bh=np.full(T,np.nan)
        for t in range(lookback,T):
            w=x[t-lookback:t]
            m=np.mean(w); wc=w-m
            v=np.dot(wc[:-1],wc[:-1]); cnum=np.dot(wc[:-1],wc[1:])
            if v>1e-12:
                b=cnum/v; bh[t]= -np.log(abs(b))/0.693 if (0<b<1) else np.nan
        hl.iloc[:,c]=bh
    return out, hl

def run(resid, entry=1.25, exit_t=0.75, sign=1, lookback=60, cost_bps=5.0):
    ss, hl = markov_zscores(resid, lookback)
    # mask: only trade where 3<HL<60
    tradable=(hl>3)&(hl<60)
    z=ss.where(tradable, 0.0)
    pos=pd.DataFrame(0.0,index=z.index,columns=z.columns)
    state={c:0.0 for c in z.columns}
    for t in z.index:
        row=z.loc[t]
        for c in z.columns:
            s=row.loc[c]
            if s==0.0 and state[c]!=0:  # not currently tradable -> flatten
                state[c]=0.0; continue
            if state[c]==0:
                if sign*s<-entry: state[c]=1.0
                elif sign*s>entry: state[c]=-1.0
            elif state[c]==1.0:
                if sign*s> -exit_t: state[c]=0.0
            elif state[c]==-1.0:
                if sign*s< exit_t: state[c]=0.0
            pos.loc[t,c]=state[c]
    gr=(pos.shift()*resid).sum(axis=1,min_count=1)
    turn=pos.diff().abs().sum(axis=1)
    net=gr-turn*cost_bps/1e4
    return net,gr,turn,pos
