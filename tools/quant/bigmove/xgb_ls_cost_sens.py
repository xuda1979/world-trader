"""Cost & robustness sensitivity for champion (K=8, vol-target 1.5%)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()
K,TARGET=8,0.015

def raw_daily(cost):
    rows=[]
    for date,g in live.groupby("date"):
        g=g.sort_values("pred_ret",ascending=False); n=len(g)
        li=list(g.index[:K]); si=list(g.index[max(0,n-K):]); nl=len(li); ns=len(si)
        if nl==0: continue
        day=(g.loc[li,"rn"]-2*cost).sum()*(1.0/nl)
        if ns>0: day += -((g.loc[si,"rn"]-2*cost).sum())*(1.0/ns)
        rows.append((date,day))
    return pd.Series(dict(rows)).sort_index()

for cost in [0.0003,0.0006,0.0010,0.0015]:
    raw=raw_daily(cost)
    rv=raw.rolling(20,min_periods=10).std().shift(1); scale=(TARGET/rv).clip(upper=3,lower=0).fillna(1)
    dser=raw*scale
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[dser.index]=dser; full=full.sort_index()
    sr=(full.mean()/full.std())*np.sqrt(252); ann=(1+full).prod()**(252/len(full))-1; dd=((1+full).cumprod()/(1+full).cumprod().cummax()-1).min()
    print(f"cost={cost}: SR={sr:.3f} ann={ann:.1%} DD={dd:.1%}")
