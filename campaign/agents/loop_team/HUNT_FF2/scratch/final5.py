"""FINAL 5: independent re-verification of the delivered poolvt file: reload from disk with a
FRESH minimal implementation (no lib.py import) and recompute every gate number."""
import numpy as np, pandas as pd
R='/Users/daxu/software/world-trader'
pv=pd.read_csv(f'{R}/campaign/agents/loop_team/HUNT_FF2/sleeves/FF2_DUALGATE_poolvt_daily.csv',
               index_col=0,parse_dates=True)['ret']
ch=pd.read_csv(f'{R}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv',index_col=0,parse_dates=True)['ret']
mu,sd=pv.mean(),pv.std()
sr=mu/sd*np.sqrt(252)
eq=(1+pv).cumprod(); mdd=(eq/eq.cummax()-1).min()
yr=pv.groupby(pv.index.year).apply(lambda x:(1+x).prod()-1)
mid=pv.index[len(pv)//2]
def srf(x): return x.mean()/x.std()*np.sqrt(252)
h1,h2=srf(pv[pv.index<=mid]),srf(pv[pv.index>mid])
j=pd.concat([pv.rename('s'),ch.rename('c')],axis=1,join='inner').dropna()
corr=j['s'].corr(j['c'])
v=pv.values
runs=1; mx=1
for i in range(1,len(v)):
    if v[i]==v[i-1] and v[i]!=0: runs+=1; mx=max(mx,runs)
    else: runs=1
print(f"INDEPENDENT RECHECK: n={len(pv)} SR_d={sr:.4f} ann_geo={((eq.iloc[-1])**(252/len(pv))-1)*100:.2f}% "
      f"MDD={mdd*100:.2f}% negy={int((yr<0).sum())} worst={yr.min()*100:.2f}% H1={h1:.3f} H2={h2:.3f} "
      f"corr={corr:+.4f} ac1={pv.autocorr(1):.4f} uniqR={pv.round(10).nunique()/len(pv):.4f} maxnzrun={mx}")
