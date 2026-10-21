"""AGENT 04: PNL RECONSTRUCTION & REPRODUCIBILITY AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report = {"agent": "04_pnl_recon", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 04: PNL RECONSTRUCTION ===")
# Full monthly file
port=df[sleeves].dot(wt)
pmf=pd.read_csv(os.path.join(D['OD'],"OPT_20V7_full_monthly.csv"),index_col=0); pmf.index=pd.to_datetime(pmf.index)
common=port.index.intersection(pmf.index)
check("Full monthly matches file", np.abs(port.loc[common]-pmf.loc[common,'ret']).max()<1e-8,
      f"max diff={np.abs(port.loc[common]-pmf.loc[common,'ret']).max():.2e}")
# OOS monthly file
pom=osdf[sleeves].dot(wt)
pomf=pd.read_csv(os.path.join(D['OD'],"OPT_20V7_oos_monthly.csv"),index_col=0); pomf.index=pd.to_datetime(pomf.index)
c2=pom.index.intersection(pomf.index)
check("OOS monthly matches file", np.abs(pom.loc[c2]-pomf.loc[c2,'ret']).max()<1e-8,
      f"max diff={np.abs(pom.loc[c2]-pomf.loc[c2,'ret']).max():.2e}")
# SR/ann/DD/DailyDD match best.json
bj=json.load(open(os.path.join(D['OD'],"OPT_20V7_best.json")))
def dd_f(r): r=r.dropna(); eq=(1+r).cumprod(); return (eq/eq.cummax()-1).min()*100
def sr(r): r=r.dropna(); r=r[r.abs()<0.5]; return r.mean()/r.std()*np.sqrt(12)
check("is_sr matches", abs(sr(isdf[sleeves].dot(wt))-bj['is_sr'])<0.003, f"v={sr(isdf[sleeves].dot(wt)):.4f} json={bj['is_sr']:.4f}")
check("oos_sr matches", abs(sr(pom)-bj['oos_sr'])<0.003, f"v={sr(pom):.4f} json={bj['oos_sr']:.4f}")
check("oos_ann matches", abs(pom.mean()*12*100*1.6-bj['oos_ann'])<0.02, f"v={pom.mean()*12*100*1.6:.4f} json={bj['oos_ann']:.4f}")
check("oos_dd matches", abs(dd_f(pom)-bj['oos_dd'])<0.01, f"v={dd_f(pom):.4f} json={bj['oos_dd']:.4f}")
# Cumulative positive
check("Cumulative return positive", (1+port).prod()-1>0, f"cum={(1+port).prod()-1:.2f}")
# Monthly distribution
check("Positive months>65%", (port>0).mean()>0.65, f"pos%={(port>0).mean()*100:.1f}%")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent04_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
