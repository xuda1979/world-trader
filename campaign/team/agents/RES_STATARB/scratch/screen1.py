#!/usr/bin/env python3
"""RES_STATARB R1 screen 1: decorrelation-first candidate scan (no backtests yet).

Families (charter): cross-sectional relative value WITHIN equities/ETFs.
  F1 kf49 sector-relative L/S: long best trailing-5d loser? NO -- mean-reversion of
     SHORT-HORIZON relative performance between industries (daily-relative z-rev),
  F2 kf49 sector-relative MOMENTUM at 21-63d,
  F3 mom10 decile L/S (Hi-Lo PRIOR 12-2),
All built T+1 causal (decide at close t on data <= t, earn t+1), LONG-ONLY-VOL untouched;
no costs needed yet (corr gate is cost-invariant for sign/level; costs only shrink SR).
Corr to champion computed on full common span AND post-2017 span.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
from bt.gates import corr_to

ROOT="/Users/daxu/software/world-trader"; SC=f"{ROOT}/campaign/team/agents/RES_STATARB/scratch"
champ=pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",parse_dates=['date']).set_index('date')['ret']

def load(p): return pd.read_csv(p,index_col=0,parse_dates=True)

def ls_from_panel(R, k, hold=1, rev=False, rank_by='ret'):
    """daily cross-sectional L/S: long top-k by trailing rank, short bottom-k (or reverse).
    R: daily % returns panel (already causal info for ranking uses PAST rows only)."""
    tr = R.rolling(21).sum() if rank_by=='sum21' else R
    tr = tr.rolling(k).mean() if rank_by=='mean' else tr
    r = R.rank(axis=1, ascending=not rev)
    rk = tr.rank(axis=1)
    long = (rk > R.shape[1]-k)
    short = (rk <= k)
    W = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    W[long] = 1.0/k; W[short] = -1.0/k
    return W

rows=[]
vw=load(f"{SC}/kf49_vw.csv"); ew=load(f"{SC}/kf49_ew.csv"); mom=load(f"{SC}/kfmom10_vw.csv")

def book(W, R, k):
    We=W.shift(1).fillna(0.0)
    return (We*R).sum(axis=1)/k

# F3: momentum decile Hi-Lo spread (t+1)
sp = (mom['D10']-mom['D1']).shift(1)/100
for nm,r in [('mom10_hilo_vw', sp)]:
    pass

cands={}
cands['mom10_hilo_vw']=(mom['D10']-mom['D1'])/100  # spread return itself (L/S daily rebal approx)
# trailing-rank sector L/S on 49 industries: rank by trailing 21d mean, long top2 short bottom2
for pnl_name,(panel) in [('vw',vw),('ew',ew)]:
    R=panel/100.0
    tr=R.rolling(21).mean()
    for k in (2,4,8):
        rk=tr.rank(axis=1)
        W=pd.DataFrame(0.0,index=R.index,columns=R.columns)
        W[rk>R.shape[1]-k]=1.0/k; W[rk<=k]=-1.0/k
        cands[f'kf49_{pnl_name}_mom21_k{k}']=book(W,R,k)
    # short-horizon reversal: rank by 1d return, fade extremes
    for k in (2,4,8):
        rk=R.rank(axis=1)
        W=pd.DataFrame(0.0,index=R.index,columns=R.columns)
        W[rk<=k]=1.0/k; W[rk>R.shape[1]-k]=-1.0/k  # long yesterday's losers
        cands[f'kf49_{pnl_name}_rev1_k{k}']=book(W,R,k)

for nm,r in cands.items():
    r=r.replace([np.inf,-np.inf],np.nan).dropna()
    r=r[r.index>='2008-01-01']
    c_all=corr_to(champ, r)
    c17=corr_to(champ[champ.index>='2017-01-01'], r[r.index>='2017-01-01'])
    print(f"{nm:24s} n={len(r):5d} corr_all={c_all:+.3f} corr_2017+={c17:+.3f} dec={'OK' if abs(c_all)<0.15 else 'REJ'}")
