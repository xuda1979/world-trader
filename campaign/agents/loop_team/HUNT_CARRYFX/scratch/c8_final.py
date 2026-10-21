"""FINAL CANDIDATE construction + variants. Composite = 4 books x dual-tf z(21,63),
carry accrual (PIT m+1), borrow 0.5%/yr on |short|, 6bps/side; then campaign-convention
vol target 10% using TRAILING 60d std SHIFT(1) (T+1 honest), clip 3.0."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]

def build(books,lbs=(21,63),carry=True,mode="blend"):
    nets=[]
    for (a,b) in books:
        zs={lb:zsig(C,a,b,lb,2.0,2.0) for lb in lbs}
        if mode=="blend":
            W=sum(zs.values())/len(zs)
        else:  # agree-gate: trade only when signs of both z's agree; size by mean |z|
            agree=(np.sign(zs[lbs[0]])==np.sign(zs[lbs[1]]))
            W=(sum(zs.values())/len(zs)).where(agree,0.0)
        sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST
        if carry:
            cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
            net=net+sig*cr.reindex(C.index).fillna(0.0)
        net=net-0.005/252*sig.abs()
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()

def vt10(r,vt=0.10,lb=60):
    s=r.copy()
    rcum=s.shift(1).rolling(lb,min_periods=lb).std()*np.sqrt(252)  # trailing, shift(1)
    scale=(vt/rcum).clip(upper=3.0).fillna(1.0)
    out=r*scale
    return out.dropna(),scale

cands={}
for mode in ("blend","agree"):
    for carry in (True,False):
        raw=build(B4,(21,63),carry,mode)
        vt,sc=vt10(raw)
        cands[f"{mode}_carry{int(carry)}"]=(raw,vt,sc)
for k,(raw,vt,sc) in cands.items():
    st=stats(vt)
    print(f"{k:<14} RAW SR={sr(raw):.3f} vol={raw.std()*np.sqrt(252)*100:.2f}% -> VT10 SR={st['SR']} vol={st['vol']}% MDD={st['MDD']} H1/H2={st['SR_H1']}/{st['SR_H2']} neg={st['negyrs']}({st['worst_yr']}%) scale mean={sc.mean():.2f} max={sc.max():.2f}")
# save the two leading candidates raw+vt
import os
os.makedirs("sleeves",exist_ok=True)
best=cands["blend_carry1"][1]
best.to_csv("sleeves/CFX4_DTF63_carry_vt10_daily.csv",header=["ret"])
cands["blend_carry0"][1].to_csv("scratch/CFX4_nocarry_vt10_daily.csv",header=["ret"])
cands["agree_carry1"][1].to_csv("scratch/CFX4_agree_vt10_daily.csv",header=["ret"])
print("saved sleeves/CFX4_DTF63_carry_vt10_daily.csv")
# gross leverage disclosure of final: per-book |sig| EW => portfolio gross before vt; x vt scale
tot=[]
for (a,b) in B4:
    zs=[zsig(C,a,b,lb,2.0,2.0) for lb in (21,63)]
    W=(sum(zs)/len(zs)).shift(1)
    tot.append(W.abs())
G=pd.concat(tot,axis=1).mean(axis=1)  # EW gross per unit
_,sc=vt10(build(B4,(21,63),True,"blend"))
gg=(G.reindex(sc.index)*sc).dropna()
print(f"FINAL gross: mean {gg.mean():.2f}x median {gg.median():.2f}x p95 {gg.quantile(.95):.2f}x max {gg.max():.2f}x")
