"""AGENT 06: ROBUSTNESS (WF, LOO, stability)"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"06_robustness","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; osdf=D['osdf']
print("=== AGENT 06: ROBUSTNESS ===")
wf=[]
for fs in range(2012,2022):
    ooss=pd.Timestamp(f"{fs+5}-01-01"); oose=pd.Timestamp(f"{fs+6}-01-01")
    win=df[sleeves][(df.index>=ooss)&(df.index<oose)]
    if len(win)>=6: wf.append(sr(win.dot(wt)))
check("WF all positive", all(s>0 for s in wf), f"min={min(wf):.3f}")
check("WF mean>3.0", np.mean(wf)>3.0, f"mean={np.mean(wf):.3f}")
loo=[]
for i in range(len(sleeves)):
    mask=[j for j in range(len(sleeves)) if j!=i]
    wl=wt.values[mask]/wt.values[mask].sum()
    loo.append(sr(osdf[[sleeves[j] for j in mask]].dot(wl)))
check("LOO all>2.0", all(s>2.0 for s in loo), f"min={min(loo):.3f}")
port=df[sleeves].dot(wt)
yr=port.groupby(port.index.year).apply(lambda x:(1+x).prod()-1)
check("0 neg years", (yr<0).sum()==0, "")
pos=osdf[sleeves].dot(wt)
check("H1>0", sr(pos[pos.index<'2021-01-01'])>0, f"{sr(pos[pos.index<'2021-01-01']):.3f}")
check("H2>0", sr(pos[pos.index>='2021-01-01'])>0, f"{sr(pos[pos.index>='2021-01-01']):.3f}")
np.random.seed(42)
pert=[]
for _ in range(100):
    wp=np.maximum(wt.values+np.random.normal(0,0.005,len(wt)),0.01); wp=wp/wp.sum()
    pert.append(sr(osdf[sleeves].dot(wp)))
check("Perturb 95%>2.5", np.percentile(pert,5)>2.5, f"5th={np.percentile(pert,5):.3f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent06_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
