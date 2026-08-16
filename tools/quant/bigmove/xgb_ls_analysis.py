"""Analyze long-short K5_equal equity: decompose long vs short leg, find drawdown driver."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; HERE=os.path.dirname(os.path.abspath(__file__))
CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet"); COST=0.0006
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

K=5
live=live.copy()
# long leg / short leg daily contributions
rows=[]
for date,g in live.groupby("date"):
    g=g.sort_values("pred_ret",ascending=False)
    long_sel=g.index[:K]; short_sel=g.index[-K:]
    lg=((g.loc[long_sel,"rn"]-2*COST).sum())
    sg=-((g.loc[short_sel,"rn"]-2*COST).sum())
    rows.append((date, lg, sg, (lg+sg)/K, lg/K, sg/K))
df=pd.DataFrame(rows,columns=["date","lg_tot","sg_tot","net_day","lg_day","sg_day"]).set_index("date").sort_index()
full=pd.Series(0.0,index=live["date"].unique()); full.loc[df.index]=df["net_day"]
eq=(1+full).cumprod(); dd=eq/eq.cummax()-1
print("net daily mean:",full.mean().round(6),"std:",full.std().round(6),"SR:",round(full.mean()/full.std()*np.sqrt(252),2))
print("\nlong leg daily mean:",df["lg_day"].mean().round(6))
print("short leg daily mean:",df["sg_day"].mean().round(6))
# drawdown windows
z=dd.reset_index(); z.columns=["date","dd"]
wd=z.loc[z["dd"].idxmin()]
print("\nMaxDD:",round(dd.min(),3),"at",wd["date"].date())
# 10 worst days (net)
worst=full.sort_values().head(10)
print("\n10 worst net days:")
for d,v in worst.items():
    r=df.loc[d]
    print(f"  {d.date()} net={v:+.4f} long={r['lg_day']:+.4f} short={r['sg_day']:+.4f}")
# long & short vol
print("\nlong daily std:",df['lg_day'].std().round(5),"short daily std:",df['sg_day'].std().round(5))
pyo=df.copy(); pyo["net"]=full.loc[df.index]
print("\ncorr(long,short) daily:",round(np.corrcoef(df['lg_day'],df['sg_day'])[0,1],3))
