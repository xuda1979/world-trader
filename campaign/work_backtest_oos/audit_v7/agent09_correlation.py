"""AGENT 09: CORRELATION & DIVERSIFICATION AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "09_correlation", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']; ddf=D['ddf']
print("=== AGENT 09: CORRELATION & DIVERSIFICATION ===")
corr_is=isdf[sleeves].corr()
u=corr_is.where(np.triu(np.ones(corr_is.shape),k=1).astype(bool))
check("Mean IS corr<0.15", u.stack().mean()<0.15, f"mean={u.stack().mean():.4f}")
corr_oos=osdf[sleeves].corr()
uo=corr_oos.where(np.triu(np.ones(corr_oos.shape),k=1).astype(bool))
check("Mean OOS corr<0.20", uo.stack().mean()<0.20, f"mean={uo.stack().mean():.4f}")
check("Max OOS corr<0.85", uo.abs().stack().max()<0.85, f"max={uo.abs().stack().max():.4f}")
# Diversification ratio
sv=isdf[sleeves].std()*np.sqrt(12)
wav=(wt*sv).sum()
pv=isdf[sleeves].dot(wt).std()*np.sqrt(12)
dr=wav/pv if pv>0 else 0
check("Div ratio>1.5", dr>1.5, f"DR={dr:.3f}")
# PCA
cov=isdf[sleeves].cov().values
from numpy.linalg import eig
ev,_=eig(cov); ev=np.sort(ev)[::-1].real
pc1=ev[0]/ev.sum()
check("PC1<45%", pc1<0.45, f"PC1={pc1*100:.1f}%")
# Monthly vol
port=df[sleeves].dot(wt)
check("Monthly vol<2%", port.std()<0.02, f"vol={port.std()*100:.2f}%")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent09_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
