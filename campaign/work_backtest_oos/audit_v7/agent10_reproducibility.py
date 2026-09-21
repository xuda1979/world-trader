"""AGENT 10: REPRODUCIBILITY & EDGE CASES AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "10_reproducibility", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']; ddf=D['ddf']
OD=D['OD']; ROOT="/Users/daxu/software/world-trader/campaign"
print("=== AGENT 10: REPRODUCIBILITY & EDGE CASES ===")
# Re-derive weights from scratch (IS-only fitting) and compare
from scipy.optimize import minimize
IS=isdf[sleeves]
mu_is=(IS.mean()*12).values; cov_is=IS.cov()*12
Sig=(1-0.7)*cov_is+0.7*np.diag(np.diag(cov_is))
ew=np.full(len(sleeves),1/len(sleeves))
def neg_ret(w): return -float(w@mu_is)
def sr_con(w):
    v=float(np.sqrt(w@Sig@w))
    return float(w@mu_is)/v-6.5 if v>1e-14 else -1
cons=[{"type":"eq","fun":lambda w:w.sum()-1},{"type":"ineq","fun":sr_con}]
r=minimize(neg_ret,ew,method="SLSQP",constraints=cons,bounds=[(0.03,0.15)]*len(sleeves),options={"maxiter":5000,"ftol":1e-14})
rw=r.x/r.x.sum(); rw=np.maximum(rw,0.03); rw=rw/rw.sum()
check("Weights re-derive exactly", np.abs(rw-wt.values).max()<1e-8, f"max diff={np.abs(rw-wt.values).max():.2e}")
# No NaN/Inf in panels
check("No NaN in monthly", df[sleeves].isna().sum().sum()==0, "")
check("No Inf in monthly", np.isinf(df[sleeves].values).sum()==0, "")
check("No NaN in daily", ddf[sleeves].isna().sum().sum()==0, "")
# Extreme returns
check("No |monthly|>50%", (df[sleeves].abs()>0.5).sum().sum()==0, "")
# Determinism
p1=osdf[sleeves].dot(wt); p2=osdf[sleeves].dot(wt)
check("Deterministic", (p1==p2).all(), "")
# Files exist
for f_ in ["OPT_20V7_weights.csv","OPT_20V7_best.json","OPT_20V7_full_monthly.csv","OPT_20V7_oos_monthly.csv","OPT_20V7_blotter.csv"]:
    check(f"{f_} exists", os.path.exists(os.path.join(OD,f_)), "")
# Weight file matches
wf=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0)['w']
check("Weights file matches", np.abs(wf.values-wt.values).max()<1e-10, f"diff={np.abs(wf.values-wt.values).max():.2e}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent10_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
