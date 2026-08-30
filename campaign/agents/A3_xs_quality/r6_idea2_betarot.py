"""r6 Idea 2 — BETA-ROTATION: monthly long bottom-beta-quintile EW, gated by FF-mkt MA200
(no momentum term). Beta = cov(name,mkt)/var(mkt) over trailing 252d (rolling, PIT).
Variant B: beta computed on FF 3-factor residuals (SMB/HML stripped)."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from r6lib import *

ff=D.ff_factors()
MKT=(ff["Mkt-RF"]).reindex(RETS.index).fillna(0.0)

def roll_beta(R, F, LB=252, resid=False):
    """Trailing LB-day beta of each name vs market factor. If resid: subtract SMB/HML first."""
    X=R.copy()
    if resid:
        smb=ff["SMB"].reindex(R.index).fillna(0.0); hml=ff["HML"].reindex(R.index).fillna(0.0)
        X=X.sub(smb,axis=0).sub(hml,axis=0)
    Fv=F.reindex(R.index).fillna(0.0)
    meanF=Fv.rolling(LB,min_periods=LB).mean()
    varF=Fv.rolling(LB,min_periods=LB).var()
    cov=pd.DataFrame(index=R.index,columns=R.columns,dtype=float)
    # efficient: cov = E[RF]-E[R]E[F]
    mR=X.rolling(LB,min_periods=LB).mean()
    prod=X.mul(Fv,axis=0)
    mprod=prod.rolling(LB,min_periods=LB).mean()
    covv=mprod.sub(mR.mul(meanF,axis=0))
    beta=covv.div(varF,axis=0).replace([np.inf,-np.inf],np.nan)
    return beta

def build_bottom_beta(beta,frac=0.2,use_gate=True,gate_win=200,gate_band=0.03,min_names=20):
    g=ma_gate(gate_win,gate_band) if use_gate else pd.Series(1.0,index=IDX)
    W=pd.DataFrame(0.0,index=IDX,columns=NAMES)
    for t in MES:
        if t not in beta.index: continue
        if use_gate and g.loc[t]<=0: continue
        row=beta.loc[t].dropna()
        if len(row)<min_names: continue
        row=row.sort_values(); nl=max(int(np.floor(len(row)*frac)),1)
        for s in row.index[:nl]: W.loc[t,s]=1.0/nl
    return W

for label,lb,resid,gated,frac,gw,gband in [
    ("b252_g200f3_20",252,False,True,0.2,200,0.03),
    ("b252_nogate_20",252,False,False,0.2,200,0.03),
    ("b252_resid_g200_20",252,True,True,0.2,200,0.03),
    ("b126_g200_20",126,False,True,0.2,200,0.03),
    ("b504_g200_20",504,False,True,0.2,200,0.03),
    ("b252_g200f3_40",252,False,True,0.4,200,0.03),
]:
    bt=roll_beta(RETS,RETS.mean(axis=1)*0+MKT,LB=lb,resid=resid)
    W=build_bottom_beta(bt,frac=frac,use_gate=gated,gate_win=gw,gate_band=gband)
    rbd=list(MES)
    net,_=wback_rb(W,RETS,rbd)
    nz=W.abs().sum(axis=1); start=nz[nz>0].index[0]
    r=sret(net,start,0.10)
    g=gates6(r); g["corr_champ"]=xcorr(r,CH); g["corr_old"]=xcorr(r,OLD)
    print(label,{k:g[k] for k in['SR','H1','H2','negYr','worst','ann','corr_champ','corr_old','ok6']},flush=True)
