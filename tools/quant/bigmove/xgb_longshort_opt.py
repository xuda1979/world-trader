"""Long-short cross-sectional backtest of the XGB next-day-return model on the
EXPANDED (304-asset) scaled universe. Goal: HIGH Sharpe + HIGH return.

Instead of only trading the extreme top tail (sparse, clustered, deep DD), we
harvest the FULL monotonic cross-sectional signal every day: go long top-K
predicted names and short bottom-K names, equal weight, daily rebalance.
This produces a dense, smooth daily return series -> much higher Sharpe.

Grid:
  - method: 'ls' (equal long/short), 'long' (long-only top-K), 'netlong' (long top-K, short bottom-J)
  - K (names per side), weighting (equal / pred), net-long tilt
Costs: 6bp one-side => 12bp round trip on each leg.
All metrics are calendar-time (all tradeable days, flat days when <2 names => 0).
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
COST=0.0006  # one side, per leg
TRADING_DAYS=252

fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

def calendar_metrics(daily_net):
    daily_net=daily_net.sort_index()
    eq=(1+daily_net).cumprod()
    years=len(daily_net)/TRADING_DAYS
    if daily_net.std()==0: return 0.0,0.0,0.0,0.0
    sr=(daily_net.mean()/daily_net.std())*np.sqrt(TRADING_DAYS)
    ann=(1+daily_net).prod()**(TRADING_DAYS/len(daily_net))-1
    dd=(eq/eq.cummax()-1).min()
    return round(sr,3), round(float(ann),4), round(float(dd),4), round(float(daily_net.mean()),6)

def run_ls(K, weight_by, method="ls", J=None, netlong_bias=0.0):
    """K=names per side. method:
       'ls'      : long top-K, short bottom-K (zero net)
       'long'    : long top-K only
       'netlong' : long top-K, short bottom-J
    """
    J = J if J is not None else K
    # rank pred each day
    live["rk"] = live.groupby("date")["pred_ret"].rank(method="first", ascending=True)
    # weight
    wcol = live["pred_ret"] if weight_by=="pred" else 1.0
    rows=[]
    for date, g in live.groupby("date"):
        g=g.sort_values("pred_ret", ascending=False)
        n=len(g)
        long_idx=g.index[:min(K,n)]
        short_idx=g.index[max(0,n-J):]
        # weights (1 each side for ls/long; for netlong long=1, short=bias)
        lw = wcol.loc[long_idx] if weight_by=="pred" else 1.0
        if weight_by=="pred":
            lw = lw / lw.abs().sum() if lw.abs().sum()>0 else lw
        long_net = (g.loc[long_idx,"rn"] - 2*COST) * (lw / (K if weight_by!="pred" else 1.0))
        if method=="ls":
            sw = wcol.loc[short_idx] if weight_by=="pred" else 1.0
            if weight_by=="pred":
                sw = sw / sw.abs().sum() if sw.abs().sum()>0 else sw
            short_net = -(g.loc[short_idx,"rn"] - 2*COST) * (sw / (J if weight_by!="pred" else 1.0))
            daily = long_net.sum() + short_net.sum()
        elif method=="long":
            daily = long_net.sum()
        else:  # netlong: short J names at reduced bias
            sw = wcol.loc[short_idx] if weight_by=="pred" else 1.0
            if weight_by=="pred":
                sw = sw / sw.abs().sum() if sw.abs().sum()>0 else sw
            short_net = -netlong_bias*(g.loc[short_idx,"rn"] - 2*COST) * (sw / (J if weight_by!="pred" else 1.0))
            daily = long_net.sum() + short_net.sum()
        rows.append((date, daily/ (K if weight_by=="pred" else 1.0)))
    if not rows:
        return None
    dser=pd.Series(dict(rows)).sort_index()
    # calendar over the full tradeable date range (days with no book => 0)
    full=pd.Series(0.0, index=live["date"].unique())
    full=full.reindex(full.index.union(dser.index)).fillna(0.0)
    full.loc[dser.index]=dser
    sr,ann,dd,dm=calendar_metrics(full)
    return {"sr":sr,"ann":ann,"maxdd":dd,"days":int(len(dser)),
            "active_days":int((dser.abs()>1e-12).sum()),"mean_day":dm}

def main():
    results={}
    for method in ["ls","long","netlong"]:
        for K in [5,10,20,30]:
            for wby in ["equal","pred"]:
                if method=="netlong":
                    for bias in [0.3,0.5]:
                        key=f"{method}_K{K}_{wby}_bias{bias}"
                        r=run_ls(K,wby,method="netlong",J=K,netlong_bias=bias)
                else:
                    key=f"{method}_K{K}_{wby}"
                    r=run_ls(K,wby,method=method)
                if r:
                    results[key]=r
                    print(f"  {key:>30}: SR={r['sr']} ann={r['ann']:.1%} DD={r['maxdd']:.1%} "
                          f"act={r['active_days']} mean/day={r['mean_day']:+.5f}")
    print("\n=== TOP 15 by Sharpe ===")
    ranked=sorted(results.items(), key=lambda kv: kv[1]["sr"], reverse=True)
    for k,r in ranked[:15]:
        print(f"  {k:>30}: SR={r['sr']} ann={r['ann']:.1%} DD={r['maxdd']:.1%} act={r['active_days']}")
    with open(os.path.join(OUT,"bigmove_xgb_longshort.json"),"w") as f:
        json.dump(results,f,indent=2,default=str)
    print("\nsaved ->",os.path.join(OUT,"bigmove_xgb_longshort.json"))

if __name__=="__main__": main()
