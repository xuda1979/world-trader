"""AGENT 08: OVERFITTING DETECTION AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "08_overfitting", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 08: OVERFITTING DETECTION ===")
pos=osdf[sleeves].dot(wt); pis=isdf[sleeves].dot(wt)
is_sr=sr(pis); oos_sr=sr(pos); gap=is_sr-oos_sr
check("Gap<3.0", gap<3.0, f"gap={gap:.3f}")
check("OOS>50% of IS", oos_sr>0.5*is_sr, f"ratio={oos_sr/is_sr:.3f}")
# PSR
from numpy import sqrt
sk=stats.skew(pos.dropna()); ku=stats.kurtosis(pos.dropna()); T=len(osdf)
psr=stats.norm.cdf((oos_sr*sqrt(T-1))/sqrt(1-sk*oos_sr+(ku-1)/4*oos_sr**2))
check("PSR>0.95", psr>0.95, f"PSR={psr:.4f}")
# Split-point stability
for sy in [2015,2016,2017,2018,2019]:
    sp=pd.Timestamp(f"{sy}-01-01")
    p_is=df[sleeves][df.index<sp].dot(wt); p_os=df[sleeves][df.index>=sp].dot(wt)
    check(f"Split {sy} OOS+", sr(p_os)>2.0, f"OOS={sr(p_os):.3f}")
# Weight perturbation
np.random.seed(7)
pert=[]
for _ in range(100):
    wp=np.maximum(wt.values+np.random.normal(0,0.005,len(wt)),0.02); wp=wp/wp.sum()
    pert.append(sr(osdf[sleeves].dot(wp)))
check("Perturb 95%>3.0", np.percentile(pert,5)>3.0, f"5th={np.percentile(pert,5):.3f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent08_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
