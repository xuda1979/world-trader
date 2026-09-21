"""AGENT 05: BLOTTER (REGENERATED) AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"05_blotter","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']
print("=== AGENT 05: BLOTTER (REGENERATED) ===")
# V4C blotter
bp=os.path.join(D['OD'],"OPT_20V4C_blotter.csv")
check("V4C blotter exists", os.path.exists(bp), "")
bl=pd.read_csv(bp,parse_dates=['date'])
check("V4C records>1000", len(bl)>1000, f"{len(bl)}")
check("V4C has 22 sleeves", bl['sleeve'].nunique()==22, f"{bl['sleeve'].nunique()}")
req=['date','sleeve','instrument','side','price','price_source','qty_notional','weight_from','weight_to','cost_bps']
check("Required columns", all(c in bl.columns for c in req), "")
tq=bl['qty_notional'].sum(); n_yr=(bl['date'].max()-bl['date'].min()).days/365.25
cost=tq*6.4/n_yr/10000*100
check("Cost<1%/yr", cost<1.0, f"{cost:.4f}%/yr")
check("b=6.4", (bl['cost_bps']==6.4).all(), "")
# V4 original blotter regenerated too (the 48,000-record bug fix)
bp4=os.path.join(D['OD'],"OPT_20V4_blotter.csv")
bl4=pd.read_csv(bp4,parse_dates=['date'])
check("V4 blotter regenerated (bug fixed)", len(bl4)<10000, f"{len(bl4)} records (was 48,000)")
tq4=bl4['qty_notional'].sum(); cost4=tq4*6.4/n_yr/10000*100
check("V4 blotter cost now sane", cost4<1.0, f"{cost4:.4f}%/yr (was ~12.3%/yr)")
wmap={os.path.basename(s):wt[s] for s in sleeves}
pos_ok=all(abs(bl[bl['sleeve']==os.path.basename(s)]['weight_to'].abs().max()-wmap[os.path.basename(s)])<0.01 for s in sleeves)
check("|weight_to|=allocation", pos_ok, "")
init_ok=all(abs(bl[bl['sleeve']==os.path.basename(s)]['weight_to'].iloc[0]-wmap[os.path.basename(s)])<1e-9 for s in sleeves)
check("Initial alloc=target", init_ok, "")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent05_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
