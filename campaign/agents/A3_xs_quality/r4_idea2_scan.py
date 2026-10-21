"""r4 idea2 param scan: K, TOPK, mom window — is ANY variant gate-viable?"""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform
from r4lib import *
from r2lib import wbacktest

G=ma_gate(200,0.03)
rows=[]
for K in (8,12,20):
  for TOPK in (2,4):
    for (MOM_LB,SKIP) in ((126,21),(252,42)):
      sig_mom=px.shift(SKIP)/px.shift(MOM_LB)-1.0
      W=pd.DataFrame(0.0,index=IDX,columns=px.columns)
      for t in MES:
        if G.loc[t]<=0: continue
        i=IDX.get_loc(t)
        if i<252+5: continue
        R=RETS.iloc[i-252:i]
        keep=R.columns[R.notna().sum()>=0.8*252]
        if len(keep)<40: continue
        R=R[keep].fillna(0.0)
        C=np.nan_to_num(R.corr().values); np.fill_diagonal(C,1.0)
        C=np.clip((C+C.T)/2,-1,1)
        dist=np.sqrt(np.clip(0.5*(1-C),0,None)); np.fill_diagonal(dist,0.0)
        lab=fcluster(linkage(squareform(dist,checks=False),method="average"),t=K,criterion="maxclust")
        lab=pd.Series(lab,index=keep)
        m=sig_mom.loc[t,keep].dropna()
        if len(m)<10: continue
        cm=m.groupby(lab).mean().sort_values(ascending=False)
        picks=m[(lab.isin(cm.index[:TOPK]))&(m>0)]
        if len(picks)==0: continue
        for s in picks.index: W.loc[t,s]=1.0/len(picks)
      net,_,_=wbacktest(W,RETS)
      nz=W.abs().sum(axis=1)
      if (nz>0).sum()==0: continue
      r=sret(net,0.15,nz[nz>0].index[0]); g=gates(r)
      g["corrC"]=round(corr_champ(r),3)
      rows.append((K,TOPK,MOM_LB,SKIP,g["SR"],g["H1"],g["H2"],g["negYr"],g["worst"],g["ann"],g["corrC"]))
      print(rows[-1],flush=True)
df=pd.DataFrame(rows,columns=["K","TOPK","lb","skip","SR","H1","H2","negYr","worst","ann","corrC"])
print(df.sort_values("SR",ascending=False).to_string(index=False))
print("\nany PASS (std gates + corr<=0.3):", ((df.SR>=0.6)&(df.H1>=0.3)&(df.H2>=0.3)&(df.negYr<=2)&(df.worst>-5)&(df.corrC<=0.3)).sum())
