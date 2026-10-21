"""r4 idea2: statistical sector-momentum. PIT clusters = hierarchical clustering of
trailing 252d return correlations (expanding min 252d, no lookahead), monthly.
Top-2 clusters by mean 6-1 momentum, equal-weight members, MA200/3% gate, vt15.
Gates standard + halves>=0.4 + corr<=0.3 to champion."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from r4lib import *
from r2lib import wbacktest

G=ma_gate(200,0.03)
K=12; LB=252; MOM_LB=126; SKIP=21; TOPK=2

sig_mom=px.shift(SKIP)/px.shift(MOM_LB)-1.0
W=pd.DataFrame(0.0,index=IDX,columns=px.columns)
mes=[t for t in MES if t>=IDX[min(300,len(IDX)-1)]]
labels_hist=[]
for t in mes:
    if G.loc[t]<=0: continue
    i=IDX.get_loc(t)
    if i<LB+5: continue
    R=RETS.iloc[i-LB:i]
    keep=R.columns[R.notna().sum()>=0.8*LB]
    R=R[keep].fillna(0.0)
    if len(keep)<40: continue
    C=R.corr().values
    C=np.nan_to_num(C); np.fill_diagonal(C,1.0)
    C=np.clip((C+C.T)/2,-1,1)
    dist=np.sqrt(np.clip(0.5*(1-C),0,None))
    np.fill_diagonal(dist,0.0)
    Z=linkage(squareform(dist,checks=False),method="average")
    lab=fcluster(Z,t=K,criterion="maxclust")
    lab=pd.Series(lab,index=keep)
    m=sig_mom.loc[t,keep].dropna()
    if len(m)<10: continue
    cm=m.groupby(lab).mean().sort_values(ascending=False)
    top=cm.index[:TOPK]
    picks=m[(lab.isin(top)) & (m>0)].sort_values(ascending=False)
    if len(picks)==0: continue
    for s in picks.index: W.loc[t,s]=1.0/len(picks)

net,_,_=wbacktest(W,RETS)
nz=W.abs().sum(axis=1); start=nz[nz>0].index[0]
r=sret(net,0.15,start); g=gates(r)
g["corr_champ"]=round(corr_champ(r),3)
print("[idea2 sectmom top2 K12 vt15]",g)
picksd=(W>0).sum(axis=1); print("avg picks/day:",round(picksd[picksd>0].mean(),1),"invested days:",int((picksd>0).sum()))
np.save("/tmp/r4_idea2_W.npy",W.values)  # cache
W.to_pickle("/tmp/r4_idea2_W.pkl")
