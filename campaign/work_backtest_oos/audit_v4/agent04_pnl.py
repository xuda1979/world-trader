"""AGENT 04: PNL RECONSTRUCTION"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"04_pnl","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']; ddf=D['ddf']
print("=== AGENT 04: PNL ===")
bj=json.load(open(os.path.join(D['OD'],"OPT_20V4C_best.json")))
pom=osdf[sleeves].dot(wt); pim=isdf[sleeves].dot(wt); pfm=df[sleeves].dot(wt)
check("oos_sr matches", abs(sr(pom)-bj['oos_sr'])<0.003, f"{sr(pom):.4f} vs {bj['oos_sr']:.4f}")
check("oos_ann matches", abs(pom.mean()*12*100*1.6-bj['oos_ann'])<0.02, f"{pom.mean()*12*100*1.6:.4f} vs {bj['oos_ann']:.4f}")
check("oos_dd matches", abs(dd_f(pom)-bj['oos_dd'])<0.01, f"{dd_f(pom):.4f} vs {bj['oos_dd']:.4f}")
check("is_sr matches", abs(sr(pim)-bj['is_sr'])<0.003, "")
check("gap matches", abs((sr(pim)-sr(pom))-bj['gap'])<0.003, "")
check("neg_years=0", neg_yr(pfm)==0, "")
pmf=pd.read_csv(os.path.join(D['OD'],"OPT_20V4C_full_monthly.csv"),index_col=0); pmf.index=pd.to_datetime(pmf.index)
check("Monthly file matches", np.abs(pfm-pmf['ret']).max()<1e-8, f"{np.abs(pfm-pmf['ret']).max():.2e}")
dport=ddf[sleeves].dot(wt)
d_dd16=((1+dport*1.6).cumprod()/(1+dport*1.6).cumprod().cummax()-1).min()*100
check("Daily DD matches", abs(d_dd16-bj['raw_dd_d'])<0.01, f"{d_dd16:.4f} vs {bj['raw_dd_d']:.4f}")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent04_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
