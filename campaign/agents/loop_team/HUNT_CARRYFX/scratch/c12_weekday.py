"""Weekday conditioning verdict (charter idea 3): per-dow PnL of the z-books."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
nets=[]
for (a,b) in B4:
    zs=[zsig(C,a,b,lb) for lb in (21,63)]
    W=sum(zs)/len(zs); sig=W.shift(1)
    nets.append((sig*(R[a]-R[b])-2*sig.diff().abs()*COST-0.005/252*sig.abs()))
r=pd.concat(nets,axis=1).mean(axis=1).dropna()
g=r.groupby(r.index.dayofweek)
print("per-dow (0=Mon): mean bp/day, ann SR, n")
for dow,q in g:
    print(f"  dow{dow}: {q.mean()*1e4:+.2f}bp/d  SR={sr(q):+.2f}  n={len(q)}")
# neg year detail for both sleeves
for tag,p in [("nocarry","sleeves/CFX4_DTF21_63_raw_daily.csv"),("carry","sleeves/CFX4_DTF21_63_carry_raw_daily.csv")]:
    r=pd.read_csv(p,index_col=0,parse_dates=True)["ret"]
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg=yr[yr<0]
    print(f"{tag}: neg years = {[(int(k),round(v*100,2)) for k,v in neg.items()]}")
