"""Champion long-short config artifacts: K8, bias 1.0, vol-target 1.5%
(headline) + 1.2% (conservative) + none (aggressive). Correct 4c/day cost.
Saves equity CSV + PNG + stats. """
from __future__ import annotations
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT="/Users/daxu/software/world-trader"; OUT=os.path.join(ROOT,"tools/quant/reports")
HERE=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(HERE,"data","xgb_scaled_pred.parquet")
COST=0.0006; K=8; BIAS=1.0
fr=pd.read_parquet(CACHE); fr["date"]=pd.to_datetime(fr["date"])
live=fr.dropna(subset=["pred_ret","rn"]).copy()

def raw_daily():
    rows=[]
    for date,g in live.groupby("date"):
        g=g.sort_values("pred_ret",ascending=False); n=len(g)
        if n<2*K: continue
        li=list(g.index[:K]); si=list(g.index[max(0,n-K):])
        rows.append((date, g.loc[li,"rn"].mean()-2*COST - BIAS*(g.loc[si,"rn"].mean()-2*COST)))
    return pd.Series(dict(rows)).sort_index()
raw=raw_daily()

def apply_vt(dser,tv):
    if tv is None: return dser
    rv=dser.rolling(20,min_periods=10).std().shift(1)
    return dser*((tv/rv).clip(upper=3,lower=0).fillna(1))
def full_series(dser):
    full=pd.Series(0.0,index=live["date"].unique()); full.loc[dser.index]=dser; full=full.sort_index(); return full
def stats(full):
    eq=(1+full).cumprod(); sr=(full.mean()/full.std())*np.sqrt(252); ann=(1+full).prod()**(252/len(full))-1; dd=(eq/eq.cummax()-1).min()
    return sr,ann,dd

res={}
for tv in [None,0.012,0.015,0.02]:
    d=apply_vt(raw.copy(),tv); full=full_series(d); sr,ann,dd=stats(full)
    sp={}
    for name,(a,b) in {"A2018-2020":("2018","2021"),"B2021-2023":("2021","2024"),"C2024-2026":("2024","2027")}.items():
        seg=full.loc[(full.index>=a)&(full.index<b)]
        sp[name]=round((seg.mean()/seg.std())*np.sqrt(252),2) if len(seg)>20 and seg.std()>0 else None
    res[f"vt{tv}"]={"sr":round(sr,3),"ann":round(float(ann),4),"dd":round(float(dd),4),"sub":sp,"calmar":round(float(ann)/float(dd),2)}
    print(f"vt={tv}: SR={sr:.3f} ann={ann:.1%} DD={dd:.1%} Calmar={ann/dd:.2f} sub={sp}")

# plot headline (vt 0.015) + conservative (0.012)
plt.figure(figsize=(11,5))
for tv,lab in [(None,"vol-target none"),(0.015,"vol-target 1.5%"),(0.012,"vol-target 1.2%")]:
    d=apply_vt(raw.copy(),tv); full=full_series(d); eq=(1+full).cumprod()
    plt.plot(eq.index,eq.values,linewidth=1.1,label=lab)
plt.yscale("log"); plt.title("XGB Next-Day Long-Short (K=8, equal long/short) — scaled 304-universe, 2018-2026")
plt.ylabel("equity (log)"); plt.legend(); plt.grid(alpha=0.3); plt.tight_layout()
plt.savefig(os.path.join(OUT,"bigmove_longshort_champion_eq.png"),dpi=110)
json.dump(res,open(os.path.join(OUT,"bigmove_longshort_champion.json"),"w"),indent=2,default=str)
# save vt0.015 equity
d=apply_vt(raw.copy(),0.015); full=full_series(d); (1+full).cumprod().to_csv(os.path.join(OUT,"bigmove_longshort_champion_eq.csv"),header=["eq"])
print("saved png/json/csv")
