"""Proper episode-artifact control: take the REAL z-signal path but zero it outside the
2022-07..2022-12 GBP-crash episode. If the signal-scramble p is SMALL on this artifact too,
the signal-scramble cannot certify episode-invariance (it only certifies day-level alignment).
Also: does the operational gate pA (block-boot SR<=0) reject it?"""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
books=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]
w={}
for k,(a,b) in enumerate(books):
    w[k]=zsig(C,a,b,42).shift(1)
SIG=pd.DataFrame(w).dropna()
mask=~((SIG.index>="2022-07-01")&(SIG.index<="2022-12-31"))
SIGe=SIG.copy(); SIGe[mask]=0.0
d={k:(R[a]-R[b]).reindex(SIG.index) for k,(a,b) in enumerate(books)}
def pnl(S):
    g=sum(S[k]*d[k] for k in range(3))
    t=sum(S[k].diff().abs() for k in range(3))
    return ((g-t*COST)/3.0).dropna()
net_e=pnl(SIGe)
print(f"EPISODE version of real signal: SR={sr(net_e):.3f} vol={net_e.std()*np.sqrt(252)*100:.2f}% nonzero-days={int((SIGe!=0).any(axis=1).sum())}")
# operational gate
print(f"  block-boot pA(SR<=0) = {block_boot_p(net_e,10,200,0):.4f}")
print(f"  scrub5_SR = {scrub_sr(net_e,5):.3f}")
# signal-scramble
def sig_scramble_p_multi(SIG,d,B=10,nperm=200,seed=0):
    real=sr(pnl(SIG))
    v=SIG.values; n=len(v); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    idx=SIG.index[:n]; cnt=0
    for row in starts:
        vs=np.concatenate([v[s:s+B] for s in row])
        vs=np.concatenate([vs,v[nb*B:]])[:n]
        S=pd.DataFrame(vs,index=idx,columns=[0,1,2])
        g=sum(S[k]*d[k].reindex(idx) for k in range(3))
        t=sum(S[k].diff().abs() for k in range(3))
        if sr(((g-t*COST)/3.0).dropna())>=real: cnt+=1
    return cnt/nperm
ps=[sig_scramble_p_multi(SIGe,d,10,200,sd) for sd in range(3)]
print(f"  signal-scramble p(perm>=real) on EPISODE artifact: {[round(p,3) for p in ps]}")
# real signal for contrast
ps2=[sig_scramble_p_multi(SIG,d,10,200,sd) for sd in range(3)]
print(f"  signal-scramble p on REAL signal: {[round(p,3) for p in ps2]}")
