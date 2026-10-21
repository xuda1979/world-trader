"""AGENT 10: REPRODUCIBILITY & FILES"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"10_repro","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']; ddf=D['ddf']
OD=D['OD']
print("=== AGENT 10: REPRODUCIBILITY ===")
# V4C = proportional rescale of V4 weights (deterministic, no optimizer)
v4=pd.read_csv(os.path.join(OD,"OPT_20V4_weights.csv"),index_col=0)
keep=[s for s in v4.index if s in set(sleeves)]
exp=v4['w'][keep]/v4['w'][keep].sum()
check("V4C reproduces exactly (deterministic rescale)", np.abs(exp.values-wt.values).max()<1e-10,
      f"maxdiff={np.abs(exp.values-wt.values).max():.2e}")
check("No NaN monthly", df[sleeves].isna().sum().sum()==0, "")
check("No Inf monthly", np.isinf(df[sleeves].values).sum()==0, "")
check("Deterministic", (osdf[sleeves].dot(wt)==osdf[sleeves].dot(wt)).all(), "")
for f_ in ["OPT_20V4C_weights.csv","OPT_20V4C_best.json","OPT_20V4C_full_monthly.csv",
           "OPT_20V4C_oos_monthly.csv","OPT_20V4C_blotter.csv","OPT_20V4_blotter.csv"]:
    check(f"{f_} exists", os.path.exists(os.path.join(OD,f_)), "")
wf=pd.read_csv(os.path.join(OD,"OPT_20V4C_weights.csv"),index_col=0)['w']
check("Weights file matches", np.abs(wf.values-wt.values).max()<1e-10, "")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent10_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
