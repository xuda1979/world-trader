"""r4 idea2 near-miss doc: scramble (200 reps, cost-inclusive) on K20/TOPK2/252-42 cell."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from r4lib import *
from r2lib import wbacktest

G=ma_gate(200,0.03); K=20; TOPK=2; MOM_LB=252; SKIP=42
def build_W(scores):
    W=pd.DataFrame(0.0,index=IDX,columns=px.columns)
    for t in MES:
        if G.loc[t]<=0: continue
        i=IDX.get_loc(t)
        if i<257: continue
        R=RETS.iloc[i-252:i]
        keep=R.columns[R.notna().sum()>=0.8*252]
        if len(keep)<40: continue
        R=R[keep].fillna(0.0)
        C=np.nan_to_num(R.corr().values); np.fill_diagonal(C,1.0)
        C=np.clip((C+C.T)/2,-1,1)
        dist=np.sqrt(np.clip(0.5*(1-C),0,None)); np.fill_diagonal(dist,0.0)
        lab=fcluster(linkage(squareform(dist,checks=False),method="average"),t=K,criterion="maxclust")
        lab=pd.Series(lab,index=keep)
        m=scores.loc[t,keep].dropna()
        if len(m)<10: continue
        cm=m.groupby(lab).mean().sort_values(ascending=False)
        picks=m[(lab.isin(cm.index[:TOPK]))&(m>0)]
        if len(picks)==0: continue
        for s in picks.index: W.loc[t,s]=1.0/len(picks)
    return W

sig=px.shift(SKIP)/px.shift(MOM_LB)-1.0
e=evaluate("idea2 K20 best",build_W(sig),0.15,verbose=True)
r=e["r"]; real=r.mean()/r.std()*np.sqrt(252)
srs=scramble(build_W,sig,G,0.15,e["start"],nrep=200)
print(f"scramble: real={real:.3f} 95th={np.percentile(srs,95):.3f} p={(srs<real).mean():.3f}")
# yearly detail
yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
print("yearly:", {int(k):round(v*100,1) for k,v in yr.items()})
