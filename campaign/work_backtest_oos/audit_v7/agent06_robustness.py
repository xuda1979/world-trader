"""AGENT 06: ROBUSTNESS, WALK-FORWARD, LEAVE-ONE-OUT AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "06_robustness", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 06: ROBUSTNESS & STABILITY ===")
# Walk-forward
wf=[]
for fs in range(2012,2022):
    ooss=pd.Timestamp(f"{fs+5}-01-01"); oose=pd.Timestamp(f"{fs+6}-01-01")
    win=df[sleeves][(df.index>=ooss)&(df.index<oose)]
    if len(win)>=6: wf.append(sr(win.dot(wt)))
check("WF all positive", all(s>0 for s in wf), f"min={min(wf):.3f}")
check("WF mean>3.5", np.mean(wf)>3.5, f"mean={np.mean(wf):.3f}")
# Leave-one-out
loo=[]
for i in range(len(sleeves)):
    mask=[j for j in range(len(sleeves)) if j!=i]
    wl=wt.values[mask]/wt.values[mask].sum()
    loo.append(sr(osdf[[sleeves[j] for j in mask]].dot(wl)))
check("LOO all>2.0", all(s>2.0 for s in loo), f"min={min(loo):.3f}")
# Sub-period
port=df[sleeves].dot(wt)
yr=port.groupby(port.index.year).apply(lambda x:(1+x).prod()-1)
check("0 neg years", (yr<0).sum()==0, f"neg={int((yr<0).sum())}")
h1=sr(port[port.index<"2013-01-01"]-port[port.index<"2013-01-01"])  # placeholder
# H1/H2
pos=osdf[sleeves].dot(wt)
check("H1>0", sr(pos[pos.index<'2021-01-01'])>0, f"H1={sr(pos[pos.index<'2021-01-01']):.3f}")
check("H2>0", sr(pos[pos.index>='2021-01-01'])>0, f"H2={sr(pos[pos.index>='2021-01-01']):.3f}")
# 3-yr windows all positive
all3=True
for start in range(2009,2023,3):
    end=start+3
    win=port[(port.index>=f"{start}-01-01")&(port.index<f"{end}-01-01")]
    if len(win)>=12 and sr(win)<=0: all3=False
check("All 3yr windows positive", all3, "")
# Weight perturbation stability
np.random.seed(42)
pert=[]
for _ in range(100):
    noise=np.random.normal(0,0.005,len(wt))
    wp=np.maximum(wt.values+noise,0.02); wp=wp/wp.sum()
    pert.append(sr(osdf[sleeves].dot(wp)))
check("Perturbation 95%>3.0", np.percentile(pert,5)>3.0, f"5th={np.percentile(pert,5):.3f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent06_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
