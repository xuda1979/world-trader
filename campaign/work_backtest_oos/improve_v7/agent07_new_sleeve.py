"""A07: NEW sleeve from unused macro axis — USD basket momentum (DTWEXBGS), IS-fit.
Pre-registered: qualifies only if IS SR>=1.0, max IS corr<=0.35, coverage>=80mo.
Then joins the expansion candidate set (no OOS reveal in this agent)."""
import pandas as pd, numpy as np, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
IS_END=pd.Timestamp("2017-01-01")
d=pd.read_csv("/Users/daxu/software/world-trader/tools/quant/data/newdata/DTWEXBGS.csv")
d.columns=[c.strip() for c in d.columns]
d[d.columns[0]]=pd.to_datetime(d[d.columns[0]],errors="coerce")
d=d.dropna(subset=[d.columns[0]]).set_index(d.columns[0]).sort_index()
px=pd.to_numeric(d.iloc[:,-1],errors="coerce").dropna()
ret=px.pct_change().dropna()
# 12m momentum L/S with 10% vol target, daily -> monthly
mom=px.pct_change(252)
pos=np.sign(mom).shift(1)   # causal
r=(pos*ret).dropna()
vol=r.rolling(60).std().shift(1)
r_vt=(r*0.10/vol).dropna()
m=(1+r_vt).resample("ME").prod()-1
m=m[m.index>="2009-01-01"]
mis=m[m.index<IS_END]
sr_is=mis.mean()/mis.std()*np.sqrt(12) if mis.std()>0 else 0
# corr vs V7 sleeves (IS)
cor=[]
for s in D['sleeves']:
    q=D['isdf'][s].reindex(mis.index).fillna(0)
    if q.std()>0: cor.append(abs(mis.corr(q)))
mx=max(cor) if cor else 1
cov=(m!=0).sum()
qual = sr_is>=1.0 and mx<=0.35 and cov>=80
print(f"USD-mom sleeve: IS-SR={sr_is:.2f} maxIScorr={mx:.2f} cov={cov} -> {'QUALIFIES' if qual else 'no'}")
if qual:
    m.to_csv(os.path.join(OD,"new_sleeve_usd_mom.csv"))
    print("saved new_sleeve_usd_mom.csv for expansion test")
import json
save("agent07_new_sleeve",dict(sr_is=float(sr_is),max_corr=float(mx),cov=int(cov),qualified=bool(qual)))
