"""P1: cross-sectional short-term reversal on twelve_big (EQMOM dead-agent slate).
Mechanism: 5d losers outperform winners at daily horizon (liquidity-provision premium).
T+1, 6.4bps/side turnover, borrow 0.5%/yr on shorts. Terciles, vol-normalized signal."""
import sys; sys.path.insert(0,'.')
from libb import *
import numpy as np, pandas as pd

px=panel_closes('twelve_big')
rets=px.sort_index().pct_change()

def run(lb=5, skip=0, vwin=21, tercile=3, min_names=150, start='2008-01-01'):
    r=rets
    mom=px.shift(skip)/px.shift(skip+lb)-1.0
    vol=r.rolling(vwin).std()*np.sqrt(vwin)
    sig=mom/(vol+1e-9)
    n=r.notna().sum(axis=1)
    ok=n>=min_names
    rnk=sig.rank(axis=1,pct=True)
    k=1.0/tercile
    lm=(rnk<=k)&(sig.notna()); sm=(rnk>1-k)&(sig.notna())
    nl=lm.sum(axis=1); ns=sm.sum(axis=1)
    pos=lm.div(nl,axis=0).fillna(0)-sm.div(ns,axis=0).fillna(0)
    pos[~ok]=0.0
    pos=pos[r.index>=start]
    rr=r[r.index>=start]
    # unlevered net for vt sizing (trailing only)
    g0=book_net(pos,rr,borrow=F.BORROW)
    s=F.vol_target_scale(g0, vt=0.10, min_days=60, cap=3.0, trailing_shift=1)
    posv=pos.mul(s,axis=0)
    net=book_net(posv,rr)
    return net, posv, g0

if __name__=='__main__':
    champ=F.load_champion()
    for lb,skip in [(5,0),(5,1),(10,0),(21,0),(21,1)]:
        net,posv,g0=run(lb=lb,skip=skip)
        g,st=F.gate_battery(f'rev_lb{lb}_sk{skip}',net,posv,champ)
