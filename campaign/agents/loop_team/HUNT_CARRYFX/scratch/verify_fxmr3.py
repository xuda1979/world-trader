import sys, json, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/loop_team/VET_HONESTY/audit")
import gate_harness as gh

fxmr3=f"{ROOT}/campaign/agents/loop_team/HUNT_FXMICRO/sleeves/FXMR3_42z2_daily.csv"
r=gh.readv(fxmr3).dropna()
print("n =",len(r),"span",r.index[0].date(),"..",r.index[-1].date())
def sr(x): return float(x.mean()/x.std()*np.sqrt(252))
eq=(1+r).cumprod(); mdd=float((eq/eq.cummax()-1).min())
ann_geo=float((1+r).prod()**(252/len(r))-1); ann_ar=float(r.mean()*252)
m=(1+r).resample("ME").prod()-1
print(f"SR_d {sr(r):.4f}  ann_geo {ann_geo*100:.2f}%  ann_arith {ann_ar*100:.2f}%  vol_ann {r.std()*np.sqrt(252)*100:.2f}%  MDD {mdd*100:.2f}%")
print(f"SR_m {sr(m.dropna()):.4f}")
h=len(r)//2
print(f"SR_H1 {sr(r.iloc[:h]):.3f}  SR_H2 {sr(r.iloc[h:]):.3f}")
yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
neg=yr[yr<0]
print("neg years:",{str(k):f"{v*100:.2f}%" for k,v in neg.items()}, "| worst yr", f"{yr.min()*100:.2f}%")
x=r.values; tot=x.sum(); o=np.argsort(x)[::-1]
for k in (5,10,20,50): print(f"top-{k} days = {x[o[:k]].sum()/tot*100:.1f}% of total PnL")
for tag,p in [("H11_BAL(committed)",f"{ROOT}/campaign/results/GOAL100_HONEST11_daily_BALANCED_daily.csv"),
              ("HONEST11FIX_BAL(charter)",f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv"),
              ("HONEST11L16_BAL",f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv")]:
    h11=gh.readv(p).dropna()
    j=pd.concat([r.rename("c"),h11.rename("h")],axis=1,join="inner").dropna()
    print(f"corr vs {tag}: {j.corr().iloc[0,1]:+.4f} (n={len(j)})")
v=gh.vet(fxmr3)
print(json.dumps({k:v[k] for k in ("n08","verdict","fails","flatten","perf","corr")},default=str,indent=1))
