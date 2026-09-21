"""AGENT 07: COST & FINANCING STRESS AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "07_cost_stress", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; osdf=D['osdf']
print("=== AGENT 07: COST & FINANCING STRESS ===")
port=df[sleeves].dot(wt); port_oos=osdf[sleeves].dot(wt)
bl=pd.read_csv(os.path.join(D['OD'],"OPT_20V7_blotter.csv"))
tq=bl['qty_notional'].sum(); n_yr=17.66
# Cost at increasing bps
for bps in [6.4,10,15,20,30,50]:
    cost=tq*bps/n_yr/10000
    net=port.mean()*12-cost
    check(f"Survives {bps}bps", net>0, f"cost={cost*100:.2f}%/yr net_ann={net*100:.2f}%")
# Leverage stress
for lev in [1.0,1.6,2.0,2.5,3.0]:
    eq=(1+port*lev).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
    check(f"Lev {lev}x DD>-20%", mdd>-20, f"DD={mdd:.2f}%")
# Worst 6m
r6=port.rolling(6).apply(lambda x:(1+x).prod()-1 if len(x)==6 else np.nan).dropna()
check("Worst 6m >-10%", r6.min()>-0.10, f"worst={r6.min()*100:.2f}%")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent07_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
