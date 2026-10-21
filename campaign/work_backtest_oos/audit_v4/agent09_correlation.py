"""AGENT 09: CORRELATION & DIVERSIFICATION"""
import pandas as pd, numpy as np, json, os, sys, warnings
from numpy.linalg import eig
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"09_correlation","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 09: CORRELATION ===")
ci=isdf[sleeves].corr(); ui=ci.where(np.triu(np.ones(ci.shape),k=1).astype(bool))
check("Mean IS corr<0.15", ui.stack().mean()<0.15, f"{ui.stack().mean():.4f}")
co=osdf[sleeves].corr(); uo=co.where(np.triu(np.ones(co.shape),k=1).astype(bool))
check("Mean OOS corr<0.20", uo.stack().mean()<0.20, f"{uo.stack().mean():.4f}")
check("Max OOS corr<0.85", uo.abs().stack().max()<0.85, f"{uo.abs().stack().max():.4f}")
sv=isdf[sleeves].std()*np.sqrt(12)
dr=(wt*sv).sum()/(isdf[sleeves].dot(wt).std()*np.sqrt(12))
check("Div ratio>1.5", dr>1.5, f"DR={dr:.3f}")
cov=isdf[sleeves].cov().values
ev,_=eig(cov); ev=np.sort(ev)[::-1].real
check("PC1<45%", ev[0]/ev.sum()<0.45, f"{ev[0]/ev.sum()*100:.1f}%")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent09_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
