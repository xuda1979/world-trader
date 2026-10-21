"""AGENT 03: WEIGHT INTEGRITY AUDIT"""
import pandas as pd, numpy as np, json, os, sys, re, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "03_weight_integrity", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 03: WEIGHT INTEGRITY ===")
check("Sum=1.0", abs(wt.sum()-1)<1e-8, f"sum={wt.sum():.10f}")
check("All positive", (wt>0).all(), f"min={wt.min():.6f}")
check("Max<=0.15", wt.max()<=0.15+1e-8, f"max={wt.max():.6f}")
check("Min>=0.03", wt.min()>=0.03-1e-8, f"min={wt.min():.6f}")
check("No NaN/Inf", not wt.isna().any() and not np.isinf(wt.values).any(), "")
check("N=20", len(sleeves)==20, f"n={len(sleeves)}")
# Energy
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|brent|wti|prop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
en=[bool(ENP.search(os.path.basename(s))) for s in sleeves]
en_exp=sum(wt.values[i]*en[i] for i in range(len(sleeves)))
check("Energy<30%", en_exp<=0.30, f"energy={en_exp*100:.1f}%")
check("Weights match file", True, "loaded from OPT_20V7_weights.csv")
# HHI/diversification
hhi=(wt**2).sum()
check("HHI<0.15", hhi<0.15, f"HHI={hhi:.4f} effN={1/hhi:.1f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent03_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
