#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 6: provenance re-derivation + robustness stress tests.

(A) weights_provenance: re-derive the emitted weights CSV from the sleeve CSVs alone
    (the analogue of verify_champion's weights_repro, which is recipe-specific to SR^P).
    NOTE: this shares the optimiser code with the emitter — it is a determinism check,
    not an independent reimplementation. The INDEPENDENT structural check is
    bt/verify_champion.py's byte_repro (own algebra), which passed at 1.0e-16.
(B) tail-vintage robustness: does the improvement survive dropping the last N days
    (the champion's D7 issue is 12 rewritten tail days)?
(C) construction diagnostic: NAV-drift (canonical) vs constant-mix, same weights.
(D) covariance-window sensitivity of the fitted weights (diagnostic, not selection).
"""
import json
import sys
import numpy as np, pandas as pd
from scipy.optimize import minimize

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT + "/campaign")
import importlib.util
spec = importlib.util.spec_from_file_location("rb", ROOT + "/campaign/scripts/rawew13v2_build.py")
rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)

NAMES, PATHS, GEAR, RATE, BPS = rb.NAMES, rb.PATHS, rb.GEAR, rb.RATE, rb.BPS
IS_END, P = rb.IS_END, rb.P
OUT = ROOT + "/campaign/agents/chief/coord/ITER15_WEIGHTOPT"
D = 0.62

df = pd.DataFrame({n: rb.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
isr_all = df[df.index < IS_END]
IS_HAVE = [n for n in NAMES if isr_all[n].notna().sum() > 0]
X = isr_all[IS_HAVE].dropna()
IS_MASK = df.index < IS_END
sd = np.sqrt(np.diag((X.cov()*252).values))

def max_sharpe(mu_v, Sig_m, w_max=2.0):
    k = len(mu_v)
    f = lambda w: -(w @ mu_v)/max(np.sqrt(w @ Sig_m @ w), 1e-14)
    cons = [{"type": "eq", "fun": lambda w: w.sum()-1.0}]; bnds = [(0.0, w_max)]*k
    best = None
    for w0 in (np.full(k,1/k), np.maximum(mu_v,0)/max(np.maximum(mu_v,0).sum(),1e-12),
               (1/sd)/(1/sd).sum()):
        r = minimize(f, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter":800, "ftol":1e-12})
        if r.success and (best is None or r.fun < best.fun): best = r
    return best.x

mu = X.mean()*252; Sig = X.cov()*252
Sig_d = (1-D)*Sig.values + D*np.diag(np.diag(Sig.values))
w_refit = max_sharpe(mu.values, Sig_d)
relw_refit = pd.Series(0.0, index=NAMES); relw_refit[IS_HAVE] = w_refit
relw_refit = relw_refit / relw_refit.sum()

emitted = pd.read_csv(f"{OUT}/RAWEW16_IS_MINSHARPE_weights.csv", index_col=0).iloc[:, 0]
emitted = emitted / emitted.sum()
print("(A) WEIGHTS PROVENANCE — re-derive emitted weights from sleeve CSVs (IS only)")
print(f"    max|re-derived - emitted| = {float((relw_refit - emitted[relw_refit.index]).abs().max()):.3e}  "
      f"{'IDENTICAL' if float((relw_refit-emitted[relw_refit.index]).abs().max()) < 1e-9 else 'DIFF'}")
print()

def build_net(relw_vec, constant_mix=False):
    r = pd.Series(relw_vec, index=NAMES, dtype=float)
    if constant_mix:
        d2 = pd.DataFrame(np.tile(r.values, (len(df), 1)), index=df.index, columns=NAMES)
    else:
        nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
        d2 = nav.div(nav.mean(axis=1), axis=0).mul(r, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    return (pd.Series(port, index=df.index) - to*BPS/1e4 - np.maximum(GEAR-1, 0)*RATE/252), Wg, to

def sr(s): return float(s.mean()/s.std(ddof=1)*np.sqrt(252))
def ann(s): return float(((1+s).prod()**(252/len(s))-1)*100)
def mdd(s):
    nav = (1+s).cumprod(); return float((nav/nav.cummax()-1).min()*100)

relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
net_c, _, _ = build_net(relw_refit)
net_b, _, _ = build_net(relw_heur)

print("(B) TAIL-VINTAGE ROBUSTNESS — drop the last N days (champion D7 = 12 rewritten tail days)")
for N in (0, 12, 30, 60, 120):
    a = net_c.iloc[:len(net_c)-N] if N else net_c
    b = net_b.iloc[:len(net_b)-N] if N else net_b
    d = a - b
    print(f"    drop last {N:3d}d: cand SR {sr(a):.4f} champ SR {sr(b):.4f} dSR {sr(a)-sr(b):+.4f} | "
          f"dAnn {ann(a)-ann(b):+.4f}pp | dMDD {mdd(a)-mdd(b):+.4f}pp | mean diff {d.mean()*1e4:+.4f}bp/day")
print()

print("(C) CONSTRUCTION DIAGNOSTIC — NAV-drift (canonical) vs constant-mix, SAME weights")
for tag, cm in (("nav-drift (canonical)", False), ("constant-mix", True)):
    a, _, _ = build_net(relw_refit, constant_mix=cm)
    print(f"    {tag:22s} ann {ann(a):.4f}% SR {sr(a):.4f} MDD {mdd(a):.4f}%")
print()

print("(D) COVARIANCE-WINDOW SENSITIVITY (diagnostic — weights only, not a selection)")
for tag, sub in (("IS full 2008-2016", X), ("IS 2008-2012", X[X.index < '2013-01-01']),
                 ("IS 2012-2016", X[X.index >= '2012-01-01'])):
    m = sub.mean()*252; S = sub.cov()*252
    Sd = (1-D)*S.values + D*np.diag(np.diag(S.values))
    w = max_sharpe(m.values, Sd)
    rw = pd.Series(0.0, index=NAMES); rw[IS_HAVE] = w; rw = rw/rw.sum()
    a, _, _ = build_net(rw)
    corr = float(np.corrcoef(rw[IS_HAVE].values, relw_refit[IS_HAVE].values)[0, 1])
    print(f"    {tag:20s} corr(weights, emitted) {corr:+.4f}  ->  FULL ann {ann(a):.4f}% SR {sr(a):.4f} "
          f"MDD {mdd(a):.4f}%  (OOS SR {sr(a[a.index>=IS_END]):.4f})")
