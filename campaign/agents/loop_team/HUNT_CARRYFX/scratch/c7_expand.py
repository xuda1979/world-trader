"""Expand book set to dilute episode concentration. Candidates from FXMICRO grids:
EUR_USD/NZD_USD (cont SR 0.87). Test 4-book and 5-book composites, lbs {21,42,63}."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B3=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD")]
B4=B3+[("EUR_USD","NZD_USD")]

def composite(books,lbs=(21,42,63),carry=False,div=2.0,cap=2.0):
    nets=[]
    for (a,b) in books:
        parts=[]
        for lb in lbs:
            parts.append(zsig(C,a,b,lb,cap,div))
        W=sum(parts)/len(parts); sig=W.shift(1)
        net=sig*(R[a]-R[b])-2*sig.diff().abs()*COST
        if carry:
            cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
            net=net+sig*cr.reindex(C.index).fillna(0.0)
        net=net-0.005/252*sig.abs()
        nets.append(net)
    return pd.concat(nets,axis=1).mean(axis=1).dropna()

def year_detail(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return {int(k):round(v*100,2) for k,v in yr.items()}

for tag,books in [("B3",B3),("B4(+EURNZD)",B4)]:
    for lbs in [(42,),(21,63),(21,42,63)]:
        for carry in (False,True):
            r=composite(books,lbs,carry)
            st=stats(r)
            print(f"{tag} lbs={lbs} carry={int(carry)}: n={st['n']} SR={st['SR']} H1={st['SR_H1']}/H2={st['SR_H2']} MDD={st['MDD']} neg={st['negyrs']} worstyr={st['worst_yr']}% top20={st['top20']}% top50={st['top50']}%")
r=composite(B4,(21,42,63),True)
print("\nB4 lbs=214263 carry=True yearly:",year_detail(r))
print("B4 scrub:", {k:round(scrub_sr(r,k),2) for k in (5,10,20,50)})
x=r.dropna().values; n=len(x); srs=[]
for s0 in range(0,n-63,63):
    keep=np.ones(n,bool); keep[s0:s0+63]=False
    srs.append(sr(pd.Series(x[keep],index=r.dropna().index[keep])))
print("B4 epjackMin:",round(min(srs),2),"LOYO:",round(min(sr(r[r.index.year!=y]) for y in range(2020,2027)),2))
