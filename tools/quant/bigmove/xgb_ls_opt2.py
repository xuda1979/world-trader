"""Refined long-short optimizer: maximize Sharpe subject to MaxDD bound.
Levers: K (names/side), per-name cap, net-long bias, daily-return winsorize cap.
Search reports best configs with DD<=25%, <=30% and unconstrained.
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
COST=0.0006
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

def cal(dser):
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[dser.index]=dser; full=full.sort_index()
    eq=(1+full).cumprod(); yrs=len(full)/252
    sr=(full.mean()/full.std())*np.sqrt(252)
    ann=(1+full).prod()**(252/len(full))-1
    dd=(eq/eq.cummax()-1).min()
    return sr,ann,dd

def run(K, cap=None, bias=0.0, winsor=None):
    """cap = per-name max allocation as fraction of gross (default 1/K equal).
       bias = short weight as fraction of long weight (1.0 = balanced).
       winsor = daily book return cap (float)."""
    rows=[]
    for date,g in live.groupby("date"):
        g=g.sort_values("pred_ret",ascending=False)
        n=len(g); li=list(g.index[:min(K,n)]); si=list(g.index[max(0,n-K):])
        nl=len(li); ns=len(si)
        if nl==0: continue
        lw=1.0/nl
        lg=(g.loc[li,"rn"]-2*COST).sum()*lw
        if ns>0 and bias>0:
            sw=(bias/ns)
            sg=-((g.loc[si,"rn"]-2*COST).sum())*sw
        else:
            sg=0.0
        day=lg+sg
        if winsor is not None:
            day=max(min(day,winsor),-winsor)
        rows.append((date,day))
    if not rows: return None
    dser=pd.Series(dict(rows)).sort_index()
    sr,ann,dd=cal(dser)
    return {"sr":round(sr,3),"ann":round(float(ann),4),"dd":round(float(dd),4),
            "act":int((dser.abs()>1e-12).sum())}

def main():
    results={}
    for K in [4,5,6,8,10,12,15,20]:
        for bias in [0.4,0.6,0.8,1.0]:
            for winsor in [None,0.03,0.05,0.07]:
                key=f"K{K}_bias{bias}_w{winsor}"
                r=run(K,bias=bias,winsor=winsor)
                results[key]=r
                if r and r["sr"]>0.5:
                    print(f"  {key:>28}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act']}")
    # rank by SR with DD<=25 filter, then <=30
    ranked=sorted(results.items(),key=lambda kv:kv[1]["sr"],reverse=True)
    print("\n=== Best SR with DD <= 25% ===")
    for k,r in [x for x in ranked if x[1]["dd"]>=-0.25][:8]:
        print(f"  {k:>28}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act']}")
    print("\n=== Best SR with DD <= 35% ===")
    for k,r in [x for x in ranked if x[1]["dd"]>=-0.35][:8]:
        print(f"  {k:>28}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act']}")
    print("\n=== Overall top 8 SR ===")
    for k,r in ranked[:8]:
        print(f"  {k:>28}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act']}")
    with open(os.path.join(OUT,"bigmove_xgb_ls_opt2.json"),"w") as f:
        json.dump(results,f,indent=2,default=str)
    print("\nsaved ->",os.path.join(OUT,"bigmove_xgb_ls_opt2.json"))

if __name__=="__main__": main()
