import sys; sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_CARRYFX/scratch")
import numpy as np, pandas as pd
from cfx_lib import *
C=load_close(["GBP_USD","NZD_USD","AUD_USD","EUR_USD"])
zall=[]
for a,b in [("GBP_USD","NZD_USD"),("AUD_USD","GBP_USD"),("AUD_USD","EUR_USD"),("EUR_USD","NZD_USD")]:
    for lb in (21,63):
        sp=np.log(C[a])-np.log(C[b])
        z=(sp-sp.rolling(lb).mean())/sp.rolling(lb).std()
        zall.append(z.abs().dropna())
Z=pd.concat(zall)
print(f"|z| distribution: mean {Z.mean():.3f} p50 {Z.quantile(.5):.3f} p95 {Z.quantile(.95):.3f} p99 {Z.quantile(.99):.3f} max {Z.max():.3f}")
print(f"frac |z|>1: {(Z>1).mean()*100:.2f}%  frac |z|>2: {(Z>2).mean()*100:.4f}%")
# exact MDD of delivered sleeves
for f in ["sleeves/CFX4_DTF21_63_raw_daily.csv","sleeves/CFX4_DTF21_63_carry_raw_daily.csv"]:
    r=pd.read_csv(f,index_col=0,parse_dates=True)["ret"]
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    h=len(r)//2
    print(f"{f.split('/')[-1]}: SR={sr(r):.4f} ann_geo={((1+r).prod()**(252/len(r))-1)*100:.2f}% vol={r.std()*np.sqrt(252)*100:.2f}% MDD={mdd*100:.2f}% H1={sr(r.iloc[:h]):.3f}/H2={sr(r.iloc[h:]):.3f} neg={[(int(k),round(v*100,2)) for k,v in yr[yr<0].items()]}")
