"""SKILL_ALPHAAGB_B local lib — wraps FF2's audited lib + panel loaders."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/Users/daxu/software/world-trader')
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FF2/scratch')
import lib as F   # audited battery: net_of, vol_target_scale, gate_battery, position_lag_p, COST/BORROW
ROOT='/Users/daxu/software/world-trader'

def panel_closes(d='twelve_big'):
    import os
    D=f'{ROOT}/tools/quant/data/{d}'
    out={}
    for f in os.listdir(D):
        if f.endswith('.csv'):
            df=pd.read_csv(os.path.join(D,f),parse_dates=['date'],index_col='date')
            s=df['close'].sort_index()
            s=s[~s.index.duplicated(keep='last')]
            out[f[:-4]]=s
    px=pd.DataFrame(out).sort_index()
    return px

def load_champ():
    c=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True)
    return c.iloc[:,0]

def book_net(pos, rets, cost=F.COST, borrow=F.BORROW):
    """pos DataFrame (t-decided, dollars per unit nav, sums approx +-1), rets aligned.
    net_t = sum_j pos_{j,t-1}*r_{j,t} - turn*cost - borrow on shorts."""
    p=pos.shift(1)
    gross=(p*rets).sum(axis=1)
    turn=(p.diff().abs().sum(axis=1)/2.0)
    net=gross-turn*cost
    if borrow is not None:
        net=net-borrow*p.clip(upper=0).abs().sum(axis=1)
    return net

def book_position_lag_p(pos, rets, n=200, seed=0, min_lag=21):
    """Book-level position-lag scramble (audited convention generalised): roll every
    name's position column by the SAME random lag in [21, T-21]; recompute net incl
    per-name turnover costs + borrow; p = frac(SR_perm >= SR_real)."""
    p=pos.shift(1).fillna(0.0); r=rets.reindex(p.index).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=F.BORROW*p.clip(upper=0).abs().sum(axis=1)
    net=(p.mul(r).sum(axis=1)-turn*F.COST-bor)
    real=net.mean()/net.std()*np.sqrt(252)
    rng=np.random.default_rng(seed); T=len(p); cnt=0
    rv_=r.values
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        vs=np.roll(p.values,lag,axis=0)
        ps=pd.DataFrame(vs,index=p.index,columns=p.columns)
        nt=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
        bs=F.BORROW*ps.clip(upper=0).abs().sum(axis=1).values
        ns=pd.Series(np.nansum(vs*rv_,axis=1)-nt*F.COST-bs,index=p.index)
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, float(real)
