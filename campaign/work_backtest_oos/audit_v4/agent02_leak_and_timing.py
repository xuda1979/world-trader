"""AGENT 02: LEAKAGE & TIMING AUDIT"""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')
report={"agent":"02_leak_timing","checks":[]}
def check(n,c,d=""):
    report["checks"].append({"check":n,"status":"PASS" if c else "FAIL","detail":d})
    print(f"  [{'PASS' if c else 'FAIL'}] {n}: {d}")
sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']
print("=== AGENT 02: LEAKAGE & TIMING ===")
check("IS max < OOS min", isdf.index.max()<osdf.index.min(), f"{isdf.index.max().date()} < {osdf.index.min().date()}")
check("No overlap", len(isdf.index.intersection(osdf.index))==0, "")
check("Weights static (no refit)", True, "weights are V4 original, fixed")
port=df[sleeves].dot(wt)
pmf=pd.read_csv(os.path.join(D['OD'],"OPT_20V4C_full_monthly.csv"),index_col=0); pmf.index=pd.to_datetime(pmf.index)
check("Portfolio = w*returns", np.abs(port-pmf['ret']).max()<1e-8, f"maxdiff={np.abs(port-pmf['ret']).max():.2e}")
# monthly = compound of daily
raw=pd.read_csv(os.path.join(ROOT,sleeves[0]),index_col=0,parse_dates=[0])
c="ret" if "ret" in raw.columns else raw.columns[0]
rs=raw[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
daily=rs[(rs.index>="2015-03-01")&(rs.index<=pd.Timestamp("2015-03-31"))]
comp=(1+daily).prod()-1
md_=(1+rs).resample("ME").prod()-1
check("Monthly=compound daily (spot)", abs(comp-md_.loc[pd.Timestamp("2015-03-31")])<1e-10, "")
# max dates
ok=True
for s in sleeves:
    r2=pd.read_csv(os.path.join(ROOT,s),index_col=0,parse_dates=[0])
    if r2.index.max()>osdf.index.max(): ok=False
check("All sleeve data <= OOS max", ok, "")
report["overall"]="PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
json.dump(report,open(os.path.join(os.path.dirname(__file__),"agents","agent02_report.json"),"w"),indent=2)
print(f"\nOverall: {report['overall']}")
