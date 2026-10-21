"""ROBUSTNESS BATTERY WITH REAL POWER vs episode concentration:
 (1) scrub-k curve: SR after dropping top-k days, k=0,5,10,20,50
 (2) episode jackknife: drop each disjoint 63-day window, min SR over windows
 (3) LOYO: leave-one-year-out min SR
 (4) block-boot pA (VET G6a) + vacuous tail B for the record
Apply to: committed FXMR3, my rebuild EW-3(lb42), dual-tf (21,63), episode control."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
books=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]

def series_for(kind):
    if kind=="FXMR3_committed":
        return pd.read_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv",
                           index_col=0,parse_dates=True)["ret"].dropna()
    nets42=[book_pnl(C,a,b,42)[0] for a,b in books]
    if kind=="rebuild_lb42":  return pd.concat(nets42,axis=1).mean(axis=1).dropna()
    if kind=="dualtf_2163":
        nets=[book_pnl(C,a,b,lb)[0] for lb in (21,63) for a,b in books]
        return pd.concat(nets,axis=1).mean(axis=1).dropna()
    if kind=="dualtf_214263":
        nets=[book_pnl(C,a,b,lb)[0] for lb in (21,42,63) for a,b in books]
        return pd.concat(nets,axis=1).mean(axis=1).dropna()
    if kind=="episode_control":
        w={k:zsig(C,a,b,42).shift(1) for k,(a,b) in enumerate(books)}
        SIG=pd.DataFrame(w).dropna()
        mask=(SIG.index>="2022-07-01")&(SIG.index<="2022-12-31")
        SIGe=SIG.copy(); SIGe[~mask]=0.0
        d={k:(R[a]-R[b]).reindex(SIG.index) for k,(a,b) in enumerate(books)}
        g=sum(SIGe[k]*d[k] for k in range(3)); t=sum(SIGe[k].diff().abs() for k in range(3))
        return ((g-t*COST)/3.0).dropna()
    if kind=="diffuse_control":
        rng=np.random.default_rng(11)
        x=rng.normal(0,1.7e-3,1749)
        x=x-x.mean()+1.87*x.std()/np.sqrt(252)
        i=FXMR3.index
        return pd.Series(x[:len(i)],index=i)
    raise ValueError(kind)
FXMR3=series_for("FXMR3_committed")

def scrub_curve(r):
    x=r.dropna().values; tot=x.sum()
    o=np.argsort(x)[::-1]; out={}
    for k in (0,5,10,20,50):
        keep=np.ones(len(x),bool); keep[o[:k]]=False
        out[k]=round(sr(pd.Series(x[keep],index=r.dropna().index[keep])),2)
    return out
def ep_jack(r,win=63):
    x=r.dropna(); n=len(x); srs=[]
    for s0 in range(0,n-win,win):
        keep=np.ones(n,bool); keep[s0:s0+win]=False
        srs.append(sr(pd.Series(x.values[keep],index=x.index[keep])))
    return round(min(srs),2), round(float(np.median(srs)),2), len(srs)
def loyo(r):
    return min(sr(r[r.index.year!=y]) for y in sorted(set(r.index.year)))
def boot_pA(r,B=10,nperm=1000,seed=0):
    x=r.dropna().values; n=len(x); nb=n//B
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    srs=[sr(pd.Series(np.concatenate([x[s:s+B] for s in row])[:n])) for row in starts]
    return round(float((np.array(srs)<=0).mean()),4)
def boot_pB(r,B=10,nperm=1000,seed=0):
    x=r.dropna().values; n=len(x); nb=n//B; real=sr(r)
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n-B,size=(nperm,nb))
    srs=[sr(pd.Series(np.concatenate([x[s:s+B] for s in row])[:n])) for row in starts]
    return round(float((np.array(srs)>=real).mean()),4)

print(f"{'series':<16} {'SR':>6} {'scrub5':>7} {'scrub10':>8} {'scrub20':>8} {'scrub50':>8} {'epjackMin':>9} {'LOYO':>6} {'pA(1k)':>7} {'pB(1k)':>7}")
for kind in ("FXMR3_committed","rebuild_lb42","dualtf_2163","dualtf_214263","episode_control","diffuse_control"):
    r=series_for(kind)
    sc=scrub_curve(r); ej=ep_jack(r)
    print(f"{kind:<16} {sr(r):>6.2f} {sc[5]:>7.2f} {sc[10]:>8.2f} {sc[20]:>8.2f} {sc[50]:>8.2f} {ej[0]:>9.2f} {loyo(r):>6.2f} {boot_pA(r):>7.4f} {boot_pB(r):>7.4f}")
