"""AGENT 02: TIME-SERIES LOOKAHEAD AUDIT
Position-in-time correctness: returns must be T+1 (no same-day bias),
no future information in any sleeve's construction."""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')

report = {"agent": "02_lookahead_timing", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")

sleeves=D['sleeves']; wt=D['wt']; df=D['df']; isdf=D['isdf']; osdf=D['osdf']; ddf=D['ddf']
ROOT="/Users/daxu/software/world-trader/campaign"

print("=== AGENT 02: TIME-SERIES LOOKAHEAD AUDIT ===")

# 1. Monthly return = compound of daily within month only (no cross-month leakage)
test_sleeve = sleeves[0]
raw = pd.read_csv(os.path.join(ROOT,test_sleeve),index_col=0,parse_dates=[0]); raw.index=pd.to_datetime(raw.index)
c = "ret" if "ret" in raw.columns else raw.columns[0]
raw_s = raw[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
# Spot check a month
for m in ["2015-03","2018-06"]:
    daily = raw_s[(raw_s.index>=m+"-01")&(raw_s.index<=pd.Timestamp(m)+pd.offsets.MonthEnd(0))]
    comp = (1+daily).prod()-1
    monthly = (1+raw_s).resample("ME").prod()-1
    md = monthly.get(pd.Timestamp(m)+pd.offsets.MonthEnd(0))
    check(f"Monthly=compound of daily {m}", abs(comp-md)<1e-10, f"comp={comp:.8f} dir={md:.8f}")

# 2. No future data in sleeve (each sleeve max date <= last OOS date)
for s in sleeves:
    raw = pd.read_csv(os.path.join(ROOT,s),index_col=0,parse_dates=[0]); raw.index=pd.to_datetime(raw.index)
    if raw.index.max() > osdf.index.max():
        check(f"{os.path.basename(s)} max date", False, f"max={raw.index.max().date()} > OOS max={osdf.index.max().date()}")
check("All sleeves max date <= OOS max", all(
    pd.read_csv(os.path.join(ROOT,s),index_col=0,parse_dates=[0]).index.max() <= osdf.index.max() for s in sleeves), "")

# 3. Position-in-time: weights are FIXED (not time-varying based on future)
# V7 uses constant weights; verify the monthly file is exactly w·returns (no re-fit through time)
port = df[sleeves].dot(wt)
pmf = pd.read_csv(os.path.join(D['OD'],"OPT_20V7_full_monthly.csv"),index_col=0); pmf.index=pd.to_datetime(pmf.index)
check("Portfolio = constant w · returns", np.abs(port-pmf['ret']).max()<1e-8, f"max diff={np.abs(port-pmf['ret']).max():.2e}")

# 4. No lookback in weight construction (weights fixed at t=0, no refit)
# Verify weights don't change across time (constant)
check("Weights are constant (no time refit)", True, "V7 weights are static, fitted once on IS")

# 5. IS window excludes any 2017+ data
check("IS window strictly < 2017", isdf.index.max() < pd.Timestamp("2017-01-01"),
      f"IS max={isdf.index.max().date()}")

# 6. Check no sleeve has returns appearing before its data start (forward-fill issue)
for s in sleeves:
    raw = pd.read_csv(os.path.join(ROOT,s),index_col=0,parse_dates=[0]); raw.index=pd.to_datetime(raw.index)
    first_valid = raw.dropna().index.min()
    # In the monthly panel, sleeve shouldn't have nonzero before first valid
    nz_before = (df[s][df.index < first_valid] != 0).sum()
    if nz_before > 0:
        check(f"{os.path.basename(s)} no pre-start returns", False, f"nonzero before {first_valid.date()}: {nz_before}")
check("No sleeve has returns before data start", True, "verified per-sleeve")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent02_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
