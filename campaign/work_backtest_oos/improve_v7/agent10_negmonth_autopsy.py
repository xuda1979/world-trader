"""A10: losing-month autopsy — per-sleeve attribution; repeat offenders?"""
import pandas as pd, numpy as np, os, sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from common import *
sl=D['sleeves']; wt=D['wt']; df=D['df']
lev=1.6
pm=lev*df[sl].dot(wt)-lev*0.6*0.053/12
mm=(1+pm).resample("ME").prod()-1
negm=mm[mm<0]
contrib=lev*df[sl].mul(wt,axis=1).resample("ME").prod().sub(1)*0  # build properly:
# monthly per-sleeve contribution: compound daily per month
cms={}
for s in sl:
    cms[s]=(1+df[s]*wt[s]*lev).resample("ME").prod()-1
C=pd.DataFrame(cms)
off=C.loc[negm.index]
off=off.sub(negm,axis=0)  # contribution to the shortfall vs 0 is just sleeve month ret
blame=(off<0).sum().sort_values(ascending=False)
print("sleeves by # losing months they were negative in (of 14-16):")
print(blame.head(6).to_string())
print("\nmean loss-month contribution per sleeve (%):")
print((off.mean()*100).sort_values().head(6).to_string())
top=blame.idxmax()
res=dict(table={k:int(v) for k,v in blame.items()},
         worst_month=mm.idxmin().strftime("%Y-%m"),worst=float(mm.min()))
print(f"\nworst month {res['worst_month']}: {res['worst']*100:.2f}%")
print("VERDICT: no single sleeve dominates losing months" if blame.max()<0.6*len(negm)
      else f"WARNING: {top} negative in {blame.max()}/{len(negm)} loss months -> IS-justified cap candidate")
save("agent10_autopsy",res)
