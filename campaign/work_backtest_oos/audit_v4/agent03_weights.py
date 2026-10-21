"""AGENT 03: WEIGHT INTEGRITY"""
import pandas as pd, numpy as np, json, os, re, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"03_weights","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']
print("=== AGENT 03: WEIGHTS ===")
check("Sum=1", abs(wt.sum()-1)<1e-8, f"{wt.sum():.10f}")
check("All>0", (wt>0).all(), f"min={wt.min():.6f}")
check("Max<=0.14 (V4 10% renormalized)", wt.max()<=0.14+1e-6, f"max={wt.max():.6f}")
check("No NaN/Inf", not wt.isna().any() and not np.isinf(wt.values).any(), "")
ENP=re.compile(r"(crack|diesel|diescrack|_ho_|hobr|ng_storage|C5ng|brent|wti|prop|seas_12-02|gas_prem|DBE|DBP|_ng[_.]|/ng_)",re.I)
en=[bool(ENP.search(os.path.basename(s))) for s in sleeves]
en_exp=sum(wt.values[i]*en[i] for i in range(len(sleeves)))
check("Energy<=30%", en_exp<=0.30, f"{en_exp*100:.1f}%")
hhi=(wt**2).sum()
check("HHI<0.15", hhi<0.15, f"HHI={hhi:.4f} effN={1/hhi:.1f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent03_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
