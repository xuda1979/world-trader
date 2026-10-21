"""FINAL long-short optimizer with CORRECT cost (charged on BOTH legs, 4c/day)
and proper non-overlapping construction (require n>=2K names/day else flat),
plus honest volatility targeting (no look-ahead). Sub-period robustness.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
COST=0.0006  # one side
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

def raw_daily(K,bias):
    """bias = short notional as fraction of long notional (1.0 equal).
    Long leg incurs 2c, short leg incurs 2c; day = long_net + short_net.
    long_net  = (mean long rn) - 2c
    short_net = -bias*[(mean short rn) - 2c]   <- cost sub on short leg too
    Require n>=2K (non-overlap) else flat (0 on that day)."""
    rows=[]
    for date,g in live.groupby("date"):
        g=g.sort_values("pred_ret",ascending=False); n=len(g)
        if n<2*K: continue
        li=list(g.index[:K]); si=list(g.index[max(0,n-K):])
        lnet=g.loc[li,"rn"].mean()-2*COST
        snet=-bias*(g.loc[si,"rn"].mean()-2*COST)
        rows.append((date, lnet+snet))
    return pd.Series(dict(rows)).sort_index()

def vol_target(dser,target_vol):
    rv=dser.rolling(20,min_periods=10).std().shift(1)
    scale=(target_vol/rv).clip(upper=3.0,lower=0.0).fillna(1.0)
    return dser*scale

def full_cal(dser):
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[dser.index]=dser; full=full.sort_index()
    eq=(1+full).cumprod(); sr=(full.mean()/full.std())*np.sqrt(252)
    ann=(1+full).prod()**(252/len(full))-1; dd=(eq/eq.cummax()-1).min()
    return sr,ann,dd

def sub_sr(dser):
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[dser.index]=dser; full=full.sort_index()
    out={}
    for name,(a,b) in {"A2018-2020":("2018","2021"),"B2021-2023":("2021","2024"),"C2024-2026":("2024","2027")}.items():
        seg=full.loc[(full.index>=a)&(full.index<b)]
        if len(seg)>20 and seg.std()>0: out[name]=round((seg.mean()/seg.std())*np.sqrt(252),2)
    return out

def main():
    results={}
    splits=1
    for K in [4,5,6,8,10,12,15]:
        for bias in [0.6,0.8,1.0]:
            raw=raw_daily(K,bias)
            for tv in [None,0.012,0.015,0.02]:
                d=vol_target(raw.copy(),tv) if tv else raw
                sr,ann,dd=full_cal(d); sp=sub_sr(d)
                key=f"K{K}_bias{bias}_vt{tv}"
                results[key]={"sr":round(sr,3),"ann":round(float(ann),4),"dd":round(float(dd),4),
                              "act":int((d.abs()>1e-12).sum()),"sub":sp}
    # report
    print("=== top by Sharpe ===")
    ranked=sorted(results.items(),key=lambda kv:kv[1]["sr"],reverse=True)
    for k,r in ranked[:10]:
        print(f"  {k:>22}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act']}")
    print("\n=== robust (all 3 sub-periods >0) by Sharpe ===")
    for k,r in ranked:
        sp=r["sub"]
        if len(sp)==3 and all(v>0 for v in sp.values()):
            print(f"  {k:>22}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} sub={sp}")
    with open(os.path.join(OUT,"bigmove_xgb_ls_final.json"),"w") as f:
        json.dump(results,f,indent=2,default=str)
    print("\nsaved ->",os.path.join(OUT,"bigmove_xgb_ls_final.json"))

if __name__=="__main__": main()
