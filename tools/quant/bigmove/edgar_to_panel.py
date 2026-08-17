"""Integrate EDGAR point-in-time fundamentals into the GKX monthly panel.
Builds bm, size, roe, gp_a, op_a, acc, inv chars on the union universe."""
from __future__ import annotations
import os, sys, json, glob
import numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
from edgar_fundamentals import parse_facts, facts_to_panel
from union_panel import load_union

def build_edgar_chars():
    P=load_union(); c=P["close"]
    midx=pd.DatetimeIndex(c.index).to_series().resample("ME").last()
    facts_all={}
    for fp in glob.glob(os.path.join(HERE,"data","edgar_facts","*.json")):
        t=os.path.basename(fp)[:-5]
        f=parse_facts(fp)
        if f: facts_all[t]=f
    base=facts_to_panel(facts_all, midx)
    # monthly price per ticker
    mclose=c.resample("ME").last()
    # vectorized mcap lookup: price at that month for that ticker
    pr=mclose.stack().rename("px"); pr.index.names=["month","ticker"]
    base=base.set_index(["month","ticker"])
    base["mcap"]=pr.reindex(base.index).to_numpy()
    base=base.reset_index()
    base["size"]=np.log((base["shares"]*base["mcap"]).replace(0,np.nan))
    base["bm"]=base["book_equity"]/base["mcap"].replace(0,np.nan)
    base["roe"]=base["net_income"]/base["book_equity"].replace(0,np.nan)
    # investment: asset growth YoY per ticker (point-in-time-ish via period)
    base=base.sort_values(["ticker","month"])
    base["assets_12m"]=base.groupby("ticker")["assets"].shift(4)
    base["inv"]=base["assets"]/base["assets_12m"].replace(0,np.nan)-1
    base.to_parquet(os.path.join(HERE,"data","edgar_chars.parquet"))
    print("edgar chars:", base.shape)
    for k in ["bm","size","roe","gp_a","op_a","acc","inv"]:
        print(f"  {k}: {int(base[k].notna().sum()):,}")
    return base

if __name__=="__main__":
    build_edgar_chars()
