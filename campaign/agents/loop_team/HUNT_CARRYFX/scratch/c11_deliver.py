"""Deliverables: primary sleeve (no-carry), carry variant, correlations, boot stability."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
def build(books=B4,lbs=(21,63),carry=False):
    nets=[]
    for (a,b) in books:
        zs=[zsig(C,a,b,lb) for lb in lbs]
        W=sum(zs)/len(zs); sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST
        if carry:
            cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
            net=net+sig*cr.reindex(C.index).fillna(0.0)
        net=net-0.005/252*sig.abs()
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()
nc=build(carry=False); ca=build(carry=True)
nc.to_csv("sleeves/CFX4_DTF21_63_raw_daily.csv",header=["ret"])
ca.to_csv("sleeves/CFX4_DTF21_63_carry_raw_daily.csv",header=["ret"])
print(f"nocarry: SR={sr(nc):.4f} n={len(nc)} | carry: SR={sr(ca):.4f} n={len(ca)}")
fx=pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",index_col=0,parse_dates=True)["ret"].dropna()
for tag,r in [("CFX4_nocarry",nc),("CFX4_carry",ca)]:
    j=pd.concat([r.rename("c"),fx.rename("fx")],axis=1,join="inner").dropna()
    print(f"corr {tag} vs FXMR3_committed: {j.corr().iloc[0,1]:+.4f} (n={len(j)})")
# boot pA stability: 1000x x 5 seeds
def boot_pA(r,B=10,nperm=1000,seed=0):
    x=r.dropna().values; n=len(x); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    srs=[sr(pd.Series(np.concatenate([x[s:s+B] for s in row])[:n])) for row in starts]
    return float((np.array(srs)<=0).mean())
print("CFX4 block-boot pA: ",[round(boot_pA(nc,10,1000,s),4) for s in range(5)])
print("FXMR3 block-boot pA:",[round(boot_pA(fx,10,1000,s),4) for s in range(5)])
# VET harness on final primary
sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/VET_HONESTY/audit")
import gate_harness as gh, json
v=gh.vet("sleeves/CFX4_DTF21_63_raw_daily.csv")
print("VET on PRIMARY:",json.dumps({k:v[k] for k in ("n08","verdict","fails","flatten","perf","corr")},default=str))
