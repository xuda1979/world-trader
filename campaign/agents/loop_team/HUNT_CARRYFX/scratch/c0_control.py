"""POWER CONTROL for the scramble tests: build a book KNOWN to be a single-episode artifact
(long GBP crash ride 2022H2 only) with SR~1.9 — my tests must REJECT it (high p), else the
tests are toothless and my p=0.000 on FXMR3 means nothing."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
def sr(x): x=x.dropna(); return float(x.mean()/x.std()*np.sqrt(252))
# control book: long GBP/NZD spread ONLY Sep-Dec 2022 (the crash episode), 2x vol-matched ~8%
ctl=pd.Series(0.0,index=C.index)
m=(C.index>="2022-09-01")&(C.index<="2022-12-31")
d=(R["GBP_USD"]-R["NZD_USD"])
sc=pd.Series(0.0,index=C.index); sc[m]=1.0
gross=sc.shift(1)*d
turn=2*sc.diff().abs().fillna(0)
net=(gross-turn*COST).dropna()
# vol-match to ~8.5% like the real book
k=0.085/(net.std()*np.sqrt(252))
net=net*k
print(f"CONTROL (2022-GBP-episode only): SR={sr(net):.3f} vol={net.std()*np.sqrt(252)*100:.2f}% n={len(net)}")
print(f"  top20 = {np.sort(net.values)[-20:].sum()/net.sum()*100:.1f}% of PnL, top50 = {np.sort(net.values)[-50:].sum()/net.sum()*100:.1f}%")
# return block-bootstrap p(SR<=0) — the operational charter gate
p_boot=block_boot_p(net,B=10,nperm=200,seed=0)
print(f"  block-boot p(SR<=0) = {p_boot:.4f}  <- if small, this ARTIFACT passes the operational gate!")
# signal scramble equivalent for a returns-only book: block-scramble returns, p(perm>=real)
def ret_block_scramble_ge(r,B=10,nperm=200,seed=0):
    x=r.dropna().values; n=len(x); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    base=sr(r); cnt=0
    for row in starts:
        xb=np.concatenate([x[s:s+B] for s in row])
        xb=np.concatenate([xb,x[nb*B:]])[:n]
        if xb.std()>0 and xb.mean()/xb.std()*np.sqrt(252)>=base: cnt+=1
    return cnt/nperm
pge=ret_block_scramble_ge(net,10,200,0)
print(f"  ret-block scramble p(perm>=real) = {pge:.4f}")
print(f"  scrub5_SR = {scrub_sr(net,5):.3f}  (gate >=0.3)")
