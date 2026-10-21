#!/usr/bin/env python3
"""GOVERNED V8 SOLVE (2026-09-30) — the admissible version of the V8 lane.

WHAT THIS IS: the spec §4 recipe (SLSQP, IS-only) applied to the 18 admissible
sleeves (V7's 20 MINUS the 2 decay-monitor HARD stops: FXD1_KRWTRI, crossasset_rev_L8).
This is a GOVERNED CANDIDATE ONLY: system of record (V7) is NOT flipped here.
Adoption requires the operator's sign-off + the full verification harness.

WHAT IT IS NOT: the inadmissible OPT_V8 (9/19) — pre-costfix brwt5__prefix inputs,
full-period fit, no audit (adjudicated 2026-09-19, root STANDUP_LOG L176-179).

TWO STAGES:
  S1 (solver validation): re-solve the 20 V7 sleeves with this script's recipe;
     must match committed V7 weights to <= 3e-4 (the pinned S1 tolerance, spec §4.1
     — drift is the a6 F-F 202608 vintage restatement, fully attributed).
  S2 (V8-GOV solve):     re-solve on the 18 admissible sleeves; emit weights,
     daily ledger, and the comparison table vs V7 / vs A4 zero+renorm.

Recipe (V7_REPLICATION_SPEC.md §4, mirrored from replicate_from_doc.py):
  maximize IS monthly mean x 12, s.t. IS shrunk SR >= 6.5
  (Sigma = 0.3*C + 0.7*diag(C), C = IS monthly cov x 12),
  bounds [3%, 15%] per sleeve, sum 1, SLSQP maxiter 5000 ftol 1e-14, x0 = EW,
  post-solve floor 3% then renormalize. IS = monthly panel < 2017-01-01, from
  2009-01-01, fillna(0). NO OOS data touches the solve.
"""
import os, json
import numpy as np
import pandas as pd
from scipy.optimize import minimize

B = "/Users/daxu/software/world-trader/campaign"
OD = os.path.join(B, "work_backtest_oos")
IS_END = pd.Timestamp("2017-01-01")

w7_df = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)
sleeves20 = list(w7_df.index)
w7 = w7_df["w"].astype(float)


def load(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


def mon(s):
    return (1 + s).resample("ME").prod() - 1


def solve_recipe(slv):
    """spec §4 recipe on the given sleeve list. Returns weight Series."""
    panel = pd.DataFrame({s: mon(load(s)) for s in slv})
    panel = panel[panel.index >= "2009-01-01"].fillna(0)
    Xis = panel[panel.index < IS_END]
    mu = (Xis[slv].mean() * 12).values
    C = Xis[slv].cov() * 12
    Sig = 0.3 * C + 0.7 * np.diag(np.diag(C))
    n = len(slv)
    x0 = np.full(n, 1 / n)

    def neg_ret(w):
        return -float(w @ mu)

    def sr_con(w):
        v = float(np.sqrt(w @ Sig @ w))
        return float(w @ mu) / v - 6.5 if v > 1e-14 else -1

    r = minimize(neg_ret, x0, method="SLSQP",
                 constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1},
                              {"type": "ineq", "fun": sr_con}],
                 bounds=[(0.03, 0.15)] * n,
                 options={"maxiter": 5000, "ftol": 1e-14})
    w = r.x / r.x.sum()
    w = np.maximum(w, 0.03)
    w = w / w.sum()
    return pd.Series(w, index=slv), r


# ---- S1: solver validation on the 20 committed sleeves ----
w20_sol, r20 = solve_recipe(sleeves20)
wdiff = float((w20_sol - w7.reindex(sleeves20)).abs().max())
print(f"[S1 solver validation] re-solve vs committed V7 weights: max|diff| = {wdiff:.2e}")
s1_ok = wdiff <= 3e-4
print(f"                          within pinned 3e-4 tolerance: {'PASS' if s1_ok else 'FAIL'}")
print(f"                          solver: {r20.status} {r20.message} nit={r20.nit}")

# ---- S2: V8-GOV on the 18 admissible sleeves ----
HARD = [s for s in sleeves20 if ("FXD1_KRWTRI" in s) or ("crossasset_rev_L8" in s)]
slv18 = [s for s in sleeves20 if s not in HARD]
w18, r18 = solve_recipe(slv18)
print(f"\n[S2 V8-GOV solve] 18 sleeves, dropped: {[os.path.basename(h) for h in HARD]}")
print(f"                          solver: {r18.status} {r18.message} nit={r18.nit}")
w18_out = w18.round(10)
for s in w18_out.sort_values(ascending=False).index:
    print(f"  {w18_out[s] * 100:5.2f}%  {os.path.basename(s)}")
print(f"  sum = {w18.sum():.10f}")

# persist candidate artifacts (clearly labeled GOV CANDIDATE, not system of record)
w18_out.rename("w").to_csv(os.path.join(OD, "V8GOV_candidate_weights.csv"), header=["w"])
json.dump({"stage": "V8-GOV candidate (NOT system of record)",
           "s1_solver_validation_maxdiff": wdiff, "s1_pass": bool(s1_ok),
           "solver_status": int(r18.status), "solver_nit": int(r18.nit),
           "recipe": "spec §4: SLSQP IS-only, mu=max, shrunk SR>=6.5, bounds [3%,15%]",
           "dropped_hard_stops": [os.path.basename(h) for h in HARD],
           "n_sleeves": 18},
          open(os.path.join(OD, "V8GOV_candidate_meta.json"), "w"), indent=1)
print("\nwritten: V8GOV_candidate_weights.csv + V8GOV_candidate_meta.json")
