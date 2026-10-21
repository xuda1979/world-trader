"""ROOT-CAUSE the poslag p=0.085: (1) permuted-SR distribution; (2) charter's exact wording
'200x 10d-block POSITION-LAG scramble' implemented BOTH ways; (3) is the edge timing or harvest?"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=H.xs_ls(sig,k=k)

def net_from_exec(p):
    r1=on.reindex(p.index).fillna(0.0); r2=ic.reindex(p.index).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
    return (p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor).dropna()

net=net_from_exec(pos.shift(1).fillna(0))
net=net[net.index>='2008-01-01']
real=net.mean()/net.std()*np.sqrt(252)
p_all=pos.shift(1).fillna(0).reindex(net.index).fillna(0.0)
r1=on.reindex(net.index).fillna(0.0); r2=ic.reindex(net.index).fillna(0.0)

def perm_sr(pexec, lag):
    ps=pd.DataFrame(np.roll(pexec.values,lag,axis=0),index=pexec.index,columns=pexec.columns)
    turn=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
    bor=ps.clip(upper=0).abs().sum(axis=1).values*H.BORROW
    s=(ps.mul(r1).sum(axis=1)-ps.mul(r2).sum(axis=1))-turn*H.COST-bor
    s=s[s.index>='2008-01-01']
    return float(s.mean()/s.std()*np.sqrt(252))

rng=np.random.default_rng(0)
permA=[]; permB=[]
T=len(net)
for _ in range(200):
    lagA=int(rng.integers(21,T-21)); permA.append(perm_sr(p_all,lagA))
    lagB=10*int(rng.integers(3,(T-30)//10)); permB.append(perm_sr(p_all,lagB))
permA=np.array(permA); permB=np.array(permB)
print(f'real SR {real:.3f}')
print(f'(a) any-lag shift: p={np.mean(permA>=real):.3f} permSR mean {permA.mean():.2f} q25 {np.quantile(permA,.25):.2f} q75 {np.quantile(permA,.75):.2f} max {permA.max():.2f}')
print(f'(b) 10d-block lags: p={np.mean(permB>=real):.3f} permSR mean {permB.mean():.2f} q75 {np.quantile(permB,.75):.2f} max {permB.max():.2f}')
# (c) block PERMUTATION of 10d blocks (shuffle block order, keep within-block path)
def block_perm_sr(nblocks=10, seed=0):
    rg=np.random.default_rng(seed)
    n=len(net); nb=n//nblocks
    order=rg.permutation(nb)
    idx=[]
    for b in order:
        idx.extend(range(b*nblocks,(b+1)*nblocks))
    idx=np.array(idx)
    ps=p_all.iloc[idx]
    turn=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
    bor=ps.clip(upper=0).abs().sum(axis=1).values*H.BORROW
    s=(ps.mul(r1.iloc[idx]).sum(axis=1)-ps.mul(r2.iloc[idx]).sum(axis=1))-turn*H.COST-bor
    return float(s.mean()/s.std()*np.sqrt(252))
bp=[block_perm_sr(10,s) for s in range(200)]
print(f'(c) 10d-block permutation: p={np.mean(np.array(bp)>=real):.3f} mean {np.mean(bp):.2f} q75 {np.quantile(bp,.75):.2f}')
# decomposition: which stream carries the timing content? shift only p1 (ON leg), keep p2 fixed; and vice versa
def partial_perm(leg, lag):
    ps=p_all.copy()
    if leg in ('on','both'): ps=pd.DataFrame(np.roll(ps.values,lag,axis=0),index=ps.index,columns=ps.columns)
    turn=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
    bor=ps.clip(upper=0).abs().sum(axis=1).values*H.BORROW
    s=(ps.mul(r1).sum(axis=1)-ps.mul(r2).sum(axis=1))-turn*H.COST-bor
    s=s[s.index>='2008-01-01']
    return float(s.mean()/s.std()*np.sqrt(252))
pA=[];pB=[]
for _ in range(200):
    lag=int(rng.integers(21,T-21))
    pA.append(partial_perm('on',lag))  # shift ON stream positions (IC stream shifts too since same matrix)
# separate-stream test: independent books
def stream_nets():
    p=pos.shift(1).fillna(0)
    r1=on.reindex(p.index).fillna(0.0); r2=ic.reindex(p.index).fillna(0.0)
    t1=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    n1=(p.mul(r1).sum(axis=1)-t1*H.COST-p.clip(upper=0).abs().sum(axis=1)*H.BORROW)
    n2=(-p.mul(r2).sum(axis=1)-t1*H.COST)
    return n1,n2
n1,n2=stream_nets()
n1=n1[n1.index>='2008-01-01']; n2=n2[n2.index>='2008-01-01']
print(f'ON-leg stream: SR {n1.mean()/n1.std()*np.sqrt(252):.3f} | -IC-leg stream: SR {n2.mean()/n2.std()*np.sqrt(252):.3f}')
# time-variation of the signal: how much do positions change over 21d?
pdec=pos.shift(1).fillna(0).reindex(net.index)
overlap21=(pdec*pdec.shift(21)).sum(axis=1)/ (pdec.abs().sum(axis=1))
print('position self-overlap 21d later: mean %.2f'%overlap21.mean())
