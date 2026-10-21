import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
R=C.pct_change()
B4=[("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]
G=[]
for (a,b) in B4:
    zs=[zsig(C,a,b,lb) for lb in (21,63)]
    G.append((sum(zs)/len(zs)).shift(1).abs())
g=pd.concat(G,axis=1).mean(axis=1).dropna()
print(f"PRIMARY gross exposure: mean {g.mean():.3f}x median {g.median():.3f}x p95 {g.quantile(.95):.3f}x max {g.max():.3f}x")
# accrual magnitudes per book
for (a,b) in B4:
    cr=carry_pit(CCY2FRED[a.split('_')[0]],CCY2FRED[b.split('_')[0]],C.index)
    print(f"  carry {a.split('_')[0]}-{b.split('_')[0]}: mean {cr.mean()*252*100:+.3f}%/yr (2019+: {cr[C.index>=C.index[0]].mean()*252*100:+.3f}%)")
