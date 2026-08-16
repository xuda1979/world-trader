"""Regime-gated long-short: deploy only when the model's recent cross-sectional
IC is favourable (no look-ahead). Hypothesis: the edge intermittently decays
(2023, 2026) -> a trailing-IC gate sits out poor regimes and lifts consistency.
Grid: gate window (20/40/60d), gate threshold (IC>0, IC>quantile). Reports
full-period + per-year SR, and compares vs no gate (baseline K8).
"""
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
COST=0.0006; K=8
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

# per-day LS returns + per-day IC
rows=[]
for date,g in live.groupby("date"):
    n=len(g)
    if n<2*K: 
        rows.append((date,np.nan,np.nan)); continue
    g=g.sort_values("pred_ret",ascending=False)
    li=g.index[:K]; si=g.index[-K:]
    day=g.loc[li,"rn"].mean()-2*COST-(g.loc[si,"rn"].mean()-2*COST)
    ic=g["pred_ret"].corr(g["rn"])
    rows.append((date,day,ic))
d=pd.DataFrame(rows,columns=["date","ls","ic"]).set_index("date").sort_index()
ic_series=d["ic"]

def backtest(gate_win, gate_thr):
    """If trailing-mean IC >= thr, deploy (scale=1); else scale=0 (flat) or 0 (off)."""
    trail=ic_series.rolling(gate_win,min_periods=gate_win//2).mean().shift(1)
    active=(trail>=gate_thr).astype(float)
    scaled=d["ls"]*active
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[scaled.index]=scaled.fillna(0); full=full.sort_index()
    eq=(1+full).cumprod(); yrs=len(full)/252
    sr=(full.mean()/full.std())*np.sqrt(252); ann=(1+full).prod()**(252/len(full))-1; dd=(eq/eq.cummax()-1).min()
    # per-year
    yr={}
    for y in range(2018,2027):
        seg=full.loc[full.index.year==y]
        if len(seg)>20 and seg.std()>0: yr[y]=round((seg.mean()/seg.std())*np.sqrt(252),2)
    return {"sr":round(sr,3),"ann":round(float(ann),4),"dd":round(float(dd),4),
            "act_pct":round(float(active.mean()),3),"years":yr}

res={}
# baseline no gate
b=backtest(60, -999); res["no_gate"]=b
print("no_gate:",b["sr"],b["ann"],b["dd"],"years",b["years"])
for win in [20,40,60]:
    for thr in [0.0,0.002,0.004]:
        r=backtest(win,thr)
        res[f"gate_w{win}_t{thr}"]=r
        print(f"gate w{win} t{thr}: SR={r['sr']} ann={r['ann']:.1%} DD={r['dd']:.1%} act={r['act_pct']:.0%}")
print("\nYears by best gates:")
for k in ["no_gate","gate_w40_t0.002","gate_w40_t0.004","gate_w60_t0.002","gate_w60_t0.004","gate_w20_t0.002"]:
    if k in res: print(f"  {k:>18}: {res[k]['years']}")
json.dump(res,open(os.path.join(OUT,"bigmove_xgb_regime_gate.json"),"w"),indent=2,default=str)
print("\nsaved -> bigmove_xgb_regime_gate.json")
