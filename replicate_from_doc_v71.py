#!/usr/bin/env python3
"""REPLICATE V7.1 FROM THE DEPLOYMENT DOCUMENT ALONE.
Reads ONLY V71_REPLICATION_SPEC.md (parses the §1 sleeve table) + raw sleeve CSVs.
Re-runs the §4 recipe (SLSQP, IS data only) to REGENERATE the V7.0 vector, then
applies the §4.2 zero+renorm transform, and verifies the result against the
committed OPT_20V71_weights.csv to the retired S1 tolerance (1e-6 on the transform
stage; the §4 re-solve stage carries V7.0's attributed a6-restatement drift and is
checked at V7_REPLICATION_SPEC.md §4.1's pinned 3e-4, per V71 spec §4.1).
Exit 0 = document alone regenerates V7.1. Exit 1 = DOCUMENT INSUFFICIENT."""
import os, re, sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT=os.path.dirname(os.path.abspath(__file__))
SPEC=os.path.join(ROOT,"campaign","work_backtest_oos","V71_REPLICATION_SPEC.md")
OD=os.path.join(ROOT,"campaign","work_backtest_oos")
doc=open(SPEC).read()

# ---- parse §1 sleeve table FROM THE DOCUMENT ----
rows=re.findall(r"^\| \d+ \| `([^`]+)` \| ([0-9.]+)% \|",doc,re.M)
assert len(rows)==20, f"expected 20 sleeve rows, parsed {len(rows)}"
sleeves=[r[0] for r in rows]
w_doc={s:float(p)/100.0 for s,p in rows}
print(f"[doc] parsed {len(sleeves)} sleeves from V71_REPLICATION_SPEC.md §1")

# ---- parse the §4.2 zeroed-sleeve names from the document ----
m=re.search(r"Zeroed sleeves[^\n]*:\s*#\d+ `([^`]+\.csv)`,\s*\n?#\d+ `([^`]+\.csv)`",doc)
assert m, "could not parse zeroed sleeves from spec"
zeroed=[m.group(1),m.group(2)]
print(f"[doc] zeroed sleeves (§4.2): {zeroed}")

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

# ---- stage 1 check: regenerated V7.0 vector vs committed V7.0 (3e-4 pinned) ----
saved7=pd.read_csv(os.path.join(OD,"OPT_20V7_weights.csv"),index_col=0)
saved7=saved7.reindex(sleeves)['w'].values
wdiff7=float(np.abs(w-saved7).max())
S1_STAGE1_TOL=3e-4
print(f"[stage1] recipe re-solve vs committed V7.0: max|diff|={wdiff7:.2e} "
      f"{'PASS' if wdiff7<S1_STAGE1_TOL else 'FAIL'} (tol {S1_STAGE1_TOL:g}; "
      "a6 F-F restatement drift, attributed per V7_REPLICATION_SPEC.md §4.1)")

# ---- §4.2 zero+renorm transform (exact arithmetic) ----
def zero_renorm(vec):
    out=vec.copy()
    for s in zeroed:
        i=[k for k,rel in enumerate(sleeves) if os.path.basename(rel)==s][0]
        out[i]=0.0
    return out/out.sum()

w71=zero_renorm(w)            # transform of the REGENERATED V7.0 vector
w71_committed_src=zero_renorm(saved7)  # transform of the COMMITTED V7.0 vector

# ---- stage 2 check: exact-arithmetic pin (1e-6 retired baseline) ----
# The §4.2 transform on the COMMITTED V7.0 vector is exact arithmetic -> must
# reproduce committed V7.1 to 1e-6 (float noise only) per V71 spec §4.1.
saved71=pd.read_csv(os.path.join(OD,"OPT_20V71_weights.csv"),index_col=0)
saved71=saved71.reindex(sleeves)['w'].values
wdiff71=float(np.abs(w71_committed_src-saved71).max())
S1_TOL=1e-6
print(f"[stage2] §4.2 transform(committed V7.0) vs committed V7.1: max|diff|={wdiff71:.2e} "
      f"{'PASS' if wdiff71<S1_TOL else 'FAIL'} (tol {S1_TOL:g}; "
      "retired S1 baseline per V71_REPLICATION_SPEC.md §4.1)")

# ---- stage 3 check: full doc path (recipe + transform) inherits stage-1 drift ----
# transform(regenerated V7.0) vs committed V7.1 is bounded by the renorm factor
# (1.135286) times the stage-1 drift; anything beyond that is a real failure.
wdiff_full=float(np.abs(w71-saved71).max())
RENORM=1.0/0.8808349436825245
S3_TOL=RENORM*S1_STAGE1_TOL
print(f"[stage3] doc path recipe+transform vs committed V7.1: max|diff|={wdiff_full:.2e} "
      f"{'PASS' if wdiff_full<S3_TOL else 'FAIL'} (tol {S3_TOL:.2e} = 1.135286 x 3e-4; "
      "inherits the attributed a6 stage-1 drift, no additional error allowed)")

# ---- §1 table itself must equal committed V7.1 (document is self-consistent) ----
wdoc=pd.Series([w_doc[s] for s in sleeves],index=sleeves).values
wdocdiff=float(np.abs(wdoc-saved71).max())
print(f"[§1] spec table vs committed V7.1: max|diff|={wdocdiff:.2e} "
      f"{'PASS' if wdocdiff<5e-7 else 'FAIL'} (table prints 6dp)")
fails=(int(not(wdiff7<S1_STAGE1_TOL))+int(not(wdiff71<S1_TOL))
       +int(not(wdocdiff<5e-7))+int(not(wdiff_full<S3_TOL)))
print("\nRESULT:", "V7.1 FULLY REPLICATED FROM THE DOCUMENT ALONE" if fails==0
      else f"DOCUMENT INSUFFICIENT — {fails} stage(s) FAILED")
sys.exit(1 if fails else 0)
