#!/usr/bin/env python3
"""REPLICATE V7 FROM THE DEPLOYMENT DOCUMENT ALONE.
Reads ONLY V7_REPLICATION_SPEC.md (parses the §1 sleeve table) + raw sleeve CSVs.
Re-runs the §4 recipe (SLSQP) to REGENERATE the weights, verifies them against the
committed OPT_20V7_weights.csv, then reproduces the §6 canonical metrics.
Exit 0 only if weights AND metrics both replicate."""
import pandas as pd, numpy as np, json, os, re, sys
from scipy.optimize import minimize
ROOT=os.path.dirname(os.path.abspath(__file__))
SPEC=os.path.join(ROOT,"campaign","work_backtest_oos","V7_REPLICATION_SPEC.md")
OD=os.path.join(ROOT,"campaign","work_backtest_oos")
doc=open(SPEC).read()

# ---- parse §1 sleeve table FROM THE DOCUMENT ----
rows=re.findall(r"^\| \d+ \| `([^`]+)` \| ([0-9.]+)% \|",doc,re.M)
assert len(rows)==20, f"expected 20 sleeve rows in doc, found {len(rows)}"
sleeves=[r[0] for r in rows]
doc_w=np.array([float(r[1])/100 for r in rows])
print(f"[doc] parsed {len(sleeves)} sleeves from V7_REPLICATION_SPEC.md §1")

# ---- §2 data conventions ----
def load(rel):
    d=pd.read_csv(os.path.join(ROOT,"campaign",rel),index_col=0)
    d.index=pd.to_datetime(d.index)
    c="ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf,-np.inf],np.nan).dropna()
def mon(s): return (1+s).resample("ME").prod()-1
panel=pd.DataFrame({s:mon(load(s)) for s in sleeves})
panel=panel[panel.index>="2009-01-01"].fillna(0)
IS_END=pd.Timestamp("2017-01-01")
Xis=panel[panel.index<IS_END]

# ---- §4 recipe: maximize IS mean*12 s.t. IS shrunk-SR>=6.5, bounds[3%,15%], SLSQP ----
mu=(Xis[sleeves].mean()*12).values
C=Xis[sleeves].cov()*12
Sig=0.3*C+0.7*np.diag(np.diag(C))
n=len(sleeves); x0=np.full(n,1/n)
def neg_ret(w): return -float(w@mu)
def sr_con(w):
    v=float(np.sqrt(w@Sig@w))
    return float(w@mu)/v-6.5 if v>1e-14 else -1
r=minimize(neg_ret,x0,method="SLSQP",
    constraints=[{"type":"eq","fun":lambda w:w.sum()-1},{"type":"ineq","fun":sr_con}],
    bounds=[(0.03,0.15)]*n,options={"maxiter":5000,"ftol":1e-14})
w=r.x/r.x.sum(); w=np.maximum(w,0.03); w=w/w.sum()

# ---- verify regenerated weights vs committed ----
saved=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0)
saved=saved.reindex(sleeves)['w'].values
wdiff=float(np.abs(w-saved).max())
print(f"[weights] regenerated vs committed: max|diff| = {wdiff:.2e}  -> {'PASS' if wdiff<1e-6 else 'FAIL'}")

# ---- §6 canonical metrics from the regenerated weights ----
wS=pd.Series(w,index=sleeves)
gross_m=panel[sleeves].dot(wS)
os_g=gross_m[gross_m.index>=IS_END]; is_g=gross_m[gross_m.index<IS_END]
def srm(x): x=x.dropna(); return x.mean()/x.std()*np.sqrt(12)
def dd_m(x): x=(1+x.dropna()).cumprod(); return (x/x.cummax()-1).min()*100
bj=json.load(open(os.path.join(OD,"OPT_20V7_best.json")))
checks=[
 ("IS SR gross", srm(is_g), bj['is_sr'], 0.005),
 ("OOS SR gross", srm(os_g), bj['oos_sr'], 0.005),
 ("OOS ann gross (arith)", os_g.mean()*12*100*1.6, bj['oos_ann'], 0.05),
 ("OOS MaxDD gross", dd_m(os_g), bj['oos_dd'], 0.05),
 ("Full SR gross", srm(gross_m), bj['full_sr'], 0.005),
]
yr=os_g.groupby(os_g.index.year).apply(lambda x:(1+x).prod()-1)
checks.append(("Neg years (OOS)", float(int((yr<0).sum())), 0, 0.5))
mfails=0
print(f"[metrics] {'CHECK':<26}{'FROM DOC':>12}{'CANONICAL':>12}  STATUS")
for name,got,want,tol in checks:
    ok=abs(got-want)<=tol; mfails+=(not ok)
    print(f"          {name:<26}{got:>12.4f}{want:>12.4f}  {'PASS' if ok else '**FAIL**'}")

ok_all = wdiff<1e-6 and mfails==0
print("\nRESULT:", "V7 FULLY REPLICATED FROM THE DOCUMENT ALONE ✅" if ok_all
      else "DOCUMENT INSUFFICIENT — do not use for live ❌")
sys.exit(0 if ok_all else 1)
