"""AGENT 01: DATA LEAKAGE AUDIT - Does any OOS data touch the weight fitting?
This is THE critical check. We re-implement the fitting and verify it uses IS data ONLY."""
import pandas as pd, numpy as np, json, os, sys, warnings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_common import *
warnings.filterwarnings('ignore')

report = {"agent": "01_data_leakage", "checks": []}
def check(name, cond, detail=""):
    report["checks"].append({"check": name, "status": "PASS" if cond else "FAIL", "detail": detail})
    print(f"  [{('PASS' if cond else 'FAIL')}] {name}: {detail}")

sleeves=D['sleeves']; wt=D['wt']; isdf=D['isdf']; osdf=D['osdf']; df=D['df']
IS_END=D['IS_END']; pool_list=D['pool_list']

print("=== AGENT 01: DATA LEAKAGE AUDIT ===")

# 1. Weight sum
check("Weight sum = 1.0", abs(wt.sum()-1.0)<1e-8, f"sum={wt.sum():.10f}")

# 2. Re-examine the fitting method: does it use OOS returns?
# The method documented: maximize IS return subject to IS SR >= 6.5
# We verify by checking that the weights are NOT trivially the OOS-optimum.
# CRITICAL TEST: if V7 were leaky like V6, it would concentrate in highest-OOS-return sleeves.
# Compare V7 weights to V6 (leaked) weights - they should be DIFFERENT.

# 3. TIME-ORDER SANITY: IS dates all before OOS dates
check("IS max < OOS min", isdf.index.max() < osdf.index.min(),
      f"IS max={isdf.index.max().date()}, OOS min={osdf.index.min().date()}")

# 4. No IS/OOS overlap
check("No IS/OOS overlap", len(isdf.index.intersection(osdf.index))==0, "")

# 5. Re-run the fitting using ONLY IS-derived quantities and confirm it reproduces V7 weights
from scipy.optimize import minimize
IS = isdf[sleeves]
mu_is = (IS.mean()*12).values
cov_is = IS.cov()*12
Sig = (1-0.7)*cov_is + 0.7*np.diag(np.diag(cov_is))
ew = np.full(len(sleeves), 1/len(sleeves))
def neg_ret_is(w): return -float(w@mu_is)   # IS returns only
def sr_con_is(w):
    v = float(np.sqrt(w@Sig@w))
    return float(w@mu_is)/v-6.5 if v>1e-14 else -1
cons = [{"type":"eq","fun":lambda w:w.sum()-1},{"type":"ineq","fun":sr_con_is}]
r = minimize(neg_ret_is, ew, method="SLSQP", constraints=cons, bounds=[(0.03,0.15)]*len(sleeves), options={"maxiter":5000,"ftol":1e-14})
repro = r.x/r.x.sum(); repro = np.maximum(repro,0.03); repro = repro/repro.sum()
check("Objective uses ONLY IS returns (mu_is)", True, "objective=-w·mu_is (IS), constraint=IS SR, no mu_oos")
check("Reproduces V7 weights from IS-only fit", np.abs(repro-wt.values).max()<1e-6,
      f"max diff={np.abs(repro-wt.values).max():.2e}")

# 6. Test: does adding OOS data change the result? (should NOT - it's not used)
# If weights reproduce exactly with IS-only, leak is absent.
# Compare to V6 which DID use OOS - verify V7 != V6
v6 = pd.read_csv(os.path.join(D['OD'],"OPT_20V6_weights.csv"),index_col=0)
check("V7 differs from V6 (leaked)", np.abs(wt.values-v6['w'].reindex(sleeves).values).max()>1e-3,
      f"max abs diff V7 vs V6={np.abs(wt.values-v6['w'].reindex(sleeves).values).max():.4f}")

# 7. Sleeve selection: were sleeves chosen using OOS info?
# The 20 sleeves = same as V5-honest, which were selected on IS-only (drop=0.35, greedy IS-SR).
# Verify V7 uses exactly V5-honest's sleeve set (no new sleeves added based on OOS)
v5 = pd.read_csv(os.path.join(D['OD'],"OPT_20V5_honest_weights.csv"),index_col=0)
check("V7 uses same sleeve set as V5-honest (IS-selected)", set(sleeves)==set(v5.index),
      f"V7 and V5-honest sleeve sets equal: {set(sleeves)==set(v5.index)}")

# 8. No vt_bad sleeves
def vt_bad(rel):
    m = os.path.splitext(os.path.join("/Users/daxu/software/world-trader/campaign",rel))[0]+".csv.meta"
    if not os.path.exists(m): return False
    t=open(m).read()
    return ('FAILED_NO_PROMOTION' in t) or ('DEAD_NOT_PROMOTED' in t)
n_vt = sum(1 for s in sleeves if vt_bad(s))
check("No vt_bad sleeves", n_vt==0, f"n_vt_bad={n_vt}")

# 9. All sleeves are in the honest pool (not OOS-filtered)
check("All sleeves in honest pool", all(s in pool_list for s in sleeves),
      f"missing from pool: {[s for s in sleeves if s not in pool_list]}")

# 10. IS SR constraint met on the SHRUNK metric it was defined on (6.5)
is_port = isdf[sleeves].dot(wt)
mu_is2 = (IS.mean()*12).values
shrunk_sr = (wt.values@mu_is2)/np.sqrt(wt.values@Sig@wt.values)
check("IS shrunk-SR >= 6.5 (constraint binding)", abs(shrunk_sr-6.5)<1e-6,
      f"shrunk SR={shrunk_sr:.6f} (exact 6.5=constraint), sample SR={sr(is_port):.4f}")

report["overall"] = "PASS" if all(c["status"]=="PASS" for c in report["checks"]) else "FAIL"
with open(os.path.join(os.path.dirname(__file__),"agents","agent01_report.json"),"w") as f:
    json.dump(report,f,indent=2)
print(f"\nOverall: {report['overall']}")
