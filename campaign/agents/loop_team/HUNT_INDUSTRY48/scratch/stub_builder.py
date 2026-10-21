"""DELIBERATELY BROKEN stub (same-day leak + 12bps double-side cost) to watch TDD RED."""
import numpy as np, pandas as pd
COST = 12.0/1e4
def net_of_book48(sig, R):
    ps = sig  # BUG: no shift -> same-day leak
    gross=(ps*R).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    return gross-turn*COST, ps
def poslag_scramble_p(pos,R,n=100,seed=0,min_lag=21):
    ps=pos.shift(1).fillna(0.0); r=R
    turn=(ps.diff().abs()/2.0).fillna(0.0)
    net=(ps*r-turn*COST).sum(axis=1).dropna()
    real=float(net.mean()/net.std()*np.sqrt(252))
    T=len(net); rng=np.random.default_rng(seed); cnt=0; meds=[]
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        rr=pd.DataFrame(np.roll(r.values,lag,axis=0),index=r.index,columns=r.columns)  # BUG: return-roll
        nt=(ps.diff().abs()/2.0).fillna(0.0)
        ns=(ps*rr-nt*COST).sum(axis=1).dropna()
        s=float(ns.mean()/ns.std()*np.sqrt(252)); meds.append(s)
        if s>=real: cnt+=1
    return cnt/n, float(np.median(meds))
