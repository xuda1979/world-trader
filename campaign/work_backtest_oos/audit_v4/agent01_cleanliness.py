"""AGENT 01: DISQUALIFIED-SLEEVE REMOVAL AUDIT (V4's core defect)"""
import pandas as pd, numpy as np, json, os, re, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"01_cleanliness","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']
print("=== AGENT 01: DISQUALIFIED-SLEEVE REMOVAL ===")
def vt_bad(rel):
    m=os.path.splitext(os.path.join(ROOT,rel))[0]+".csv.meta"
    if not os.path.exists(m): return False
    t=open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)
n_vt=sum(1 for s in sleeves if vt_bad(s))
check("Zero vt_bad sleeves", n_vt==0, f"count={n_vt}")
n_ov=sum(1 for s in sleeves if re.search(r"_on_CHAMP|overlay",s,re.I))
check("Zero overlay sleeves", n_ov==0, f"count={n_ov}")
n_mhx=sum(1 for s in sleeves if re.search(r"MHX|HT_TAIL",s,re.I))
check("Zero MHX/HT_TAIL", n_mhx==0, f"count={n_mhx}")
check("All sleeves in honest pool", all(s in D['pool_list'] for s in sleeves),
      f"missing={[os.path.basename(s) for s in sleeves if s not in D['pool_list']]}")
check("N=22 (27 minus 5 disqualified)", len(sleeves)==22, f"n={len(sleeves)}")
check("Weights renormalized", abs(wt.sum()-1.0)<1e-8, f"sum={wt.sum():.10f}")
# Verify weights are V4's original (proportional), not re-optimized
v4=pd.read_csv(os.path.join(D['OD'],"OPT_20V4_weights.csv"),index_col=0)
ratio=[]
for s in sleeves:
    ratio.append(wt[s]/v4['w'][s])
check("Proportional to original V4 weights (no re-opt)", max(ratio)-min(ratio)<1e-6,
      f"ratio spread={max(ratio)-min(ratio):.2e}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent01_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
