"""AGENT 08: OVERFITTING"""
import pandas as pd, numpy as np, json, os, sys, warnings
from scipy import stats
from numpy import sqrt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"08_overfitting","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 08: OVERFITTING ===")
pis=isdf[sleeves].dot(wt); pos=osdf[sleeves].dot(wt)
gap=sr(pis)-sr(pos)
check("Gap<2.5", gap<2.5, f"gap={gap:.3f}")
check("OOS>50% of IS", sr(pos)>0.5*sr(pis), f"ratio={sr(pos)/sr(pis):.3f}")
sk=stats.skew(pos.dropna()); ku=stats.kurtosis(pos.dropna()); T=len(osdf)
psr=stats.norm.cdf((sr(pos)*sqrt(T-1))/sqrt(1-sk*sr(pos)+(ku-1)/4*sr(pos)**2))
check("PSR>0.95", psr>0.95, f"PSR={psr:.4f}")
for sy in [2015,2016,2017,2018,2019]:
    sp=pd.Timestamp(f"{sy}-01-01")
    a=df[sleeves][df.index<sp].dot(wt); b=df[sleeves][df.index>=sp].dot(wt)
    check(f"Split {sy} OOS+>2", sr(b)>2.0, f"{sr(b):.3f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent08_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
