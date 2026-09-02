"""Does the SIGNAL-level block-scramble discriminate an episode artifact?
Episode book: w=+1 on the 60 best days of GBPNZD spread (cherry-picked), SR set ~1.9.
If scramble CANNOT reject it, the signal-scramble is also weak and p=0.000 on FXMR3
is not proof of episode-invariance."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD"])
R=C.pct_change()
d=(R["GBP_USD"]-R["NZD_USD"]).reindex(C.index)
# cherry-picked: w=+1 on the 60 days with the highest spread return, T+1 shifted
best=np.argsort(d.values)[::-1][:60]
w=pd.Series(0.0,index=C.index); w.iloc[best]=1.0
sig=w.shift(1).fillna(0.0)
net=(sig*d-2*sig.diff().abs().fillna(0)*COST).dropna()
print(f"EPISODE-ARTIFACT book: SR={sr(net):.3f} n_active={int((sig!=0).sum())}")
real=sr(net); n=len(sig); B=10
def sig_scramble(wsig,dsp,B,nperm,seed):
    v=wsig.values; nb=len(v)//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,len(v)-B,size=(nperm,nb))
    cnt=0
    for row in starts:
        vs=np.concatenate([v[s:s+B] for s in row])
        vs=np.concatenate([vs,v[nb*B:]])[:len(v)]
        s_=pd.Series(vs,index=wsig.index)
        n_=s_*dsp.reindex(wsig.index)-2*s_.diff().abs().fillna(0)*COST
        if sr(n_.dropna())>=real: cnt+=1
    return cnt/nperm
ps=[sig_scramble(sig,d,10,200,sd) for sd in range(3)]
print(f"signal-scramble p on ARTIFACT: {[round(p,3) for p in ps]}  <- small p = artifact PASSES (test weak)")
# now a genuinely-diffuse honest book for contrast: w=-z continuous (the real strategy family)
sp=np.log(C["GBP_USD"])-np.log(C["NZD_USD"])
z=(sp-sp.rolling(42).mean())/sp.rolling(42).std()
w2=((2.0*(-z)).clip(-2,2)/2.0).shift(1)
net2=(w2*d-2*w2.diff().abs()*COST).dropna()
real2=sr(net2)
def sig_scramble2(wsig,dsp,B,nperm,seed):
    v=wsig.dropna().values; idx=wsig.dropna().index; nb=len(v)//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,len(v)-B,size=(nperm,nb))
    cnt=0
    for row in starts:
        vs=np.concatenate([v[s:s+B] for s in row])
        vs=np.concatenate([vs,v[nb*B:]])[:len(v)]
        s_=pd.Series(vs,index=idx)
        n_=s_*dsp.reindex(idx)-2*s_.diff().abs()*COST
        if sr(n_.dropna())>=real2: cnt+=1
    return cnt/nperm
ps2=[sig_scramble2(w2,d,10,200,sd) for sd in range(3)]
print(f"honest GBPNZD book SR={real2:.2f}: signal-scramble p {[round(p,3) for p in ps2]}")
