#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — correlation-aware IS weight fit vs the champion's SR^0.55 heuristic.

MOTIVATION
  The champion's slot weights are relw_i = max(IS_SR_i, 0)^0.55, fitted at build time on
  the IS window (< 2017-01-01). That rule is a function of each sleeve's OWN SR only; it is
  blind to the covariance matrix. The pool's 4 brwt trend sleeves are 0.62-0.84 mutually
  correlated yet hold 46.9% of relw -- i.e. ~47% of the book is one bet expressed 4 times.

  For a zero-correlation asset with information ratio IR the max-Sharpe portfolio obeys
  SR_new = sqrt(SR_p^2 + IR^2), so genuinely decorrelated sleeves with POSITIVE IS SR should
  earn weight under a correlation-aware fit even though their standalone SR is far below the
  book's. This script tests exactly that, with the same IS-only discipline.

DISCIPLINE
  * Weights fitted ONLY on IS (< 2017-01-01). Single OOS reveal afterwards.
  * Construction is the canonical machinery VERBATIM (NAV-drift weights x relw, row-normalised,
    gross exactly 1.6, FULL |dW| @ 6.4bps one-side, margin 4.5%/yr on (GEAR-1)).
  * Nothing is written to the champion; this is a measurement script.
"""
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

# ---------------------------------------------------------------- data
df = pd.DataFrame({n: rb.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
isr = df[df.index < IS_END]
IS_HAVE = [n for n in NAMES if isr[n].notna().sum() > 0]     # CFX4 excluded (no IS data)
X = isr[IS_HAVE].dropna()                                     # common IS block
T = len(X)

# ---------------------------------------------------------------- canonical machinery
def build_net(relw_vec):
    """Exact replica of rawew13v2_build.build() with a caller-supplied relw vector."""
    relw = pd.Series(relw_vec, index=NAMES, dtype=float)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / 252)
    return net, Wg, to

def metrics(net, label):
    n = len(net)
    nav = (1 + net).cumprod()
    ann = float(nav.iloc[-1] ** (252 / n) - 1)
    sr = float(net.mean() / net.std(ddof=1) * np.sqrt(252))
    mdd = float((nav / nav.cummax() - 1).min())
    yr = net.groupby(net.index.year).apply(lambda r: (1 + r).prod() - 1)
    neg = int((yr < 0).sum())
    return dict(label=label, n=n, ann=ann, sr=sr, mdd=mdd, neg=neg,
                worst=float(yr.min()), first=net.index.min().date(), last=net.index.max().date())

def show(m, extra=""):
    print(f"{m['label']:34s} n={m['n']:5d} ann={m['ann']*100:7.3f}%  SR={m['sr']:6.4f}  "
          f"MDD={m['mdd']*100:7.4f}%  neg={m['neg']}  worst={m['worst']*100:+7.3f}% {extra}")

# ---------------------------------------------------------------- baseline (heuristic champion)
SR_is = pd.Series({n: rb.is_sr(isr[n]) for n in NAMES})
relw_heur = np.maximum(SR_is, 0.0) ** P
net_base, _, _ = build_net(relw_heur)
print("=" * 118)
print("BASELINE — champion heuristic relw = max(IS_SR,0)^0.55   (the committed book)")
show(metrics(net_base.loc[:IS_END - pd.Timedelta(days=1)], "   heuristic  IS"))
show(metrics(net_base.loc[IS_END:], "   heuristic  OOS"))
show(metrics(net_base, "   heuristic  FULL"))
print()

# ---------------------------------------------------------------- covariance inputs
mu = X.mean() * 252                      # annualised mean
Sig = X.cov() * 252                      # annualised covariance
sd = np.sqrt(np.diag(Sig))

def max_sharpe(mu_v, Sig_m, w_max=2.0):
    """Long-only max-Sharpe via SLSQP. Weights sum to 1 (scale-invariant for SR)."""
    k = len(mu_v)
    def neg_sharpe(w):
        v = np.sqrt(w @ Sig_m @ w)
        return -(w @ mu_v) / v if v > 1e-14 else 0.0
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0.0, w_max)] * k
    best = None
    for start in ("ew", "sr", "inv"):
        w0 = {"ew": np.full(k, 1 / k),
              "sr": np.maximum(mu_v, 0) / max(np.maximum(mu_v, 0).sum(), 1e-12),
              "inv": (1 / sd) / (1 / sd).sum()}[start]
        r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun):
            best = r
    return best.x

# shrinkage grid: Sig_d = (1-d) Sig + d diag(Sig)
print("=" * 118)
print("IS-FITTED LONG-ONLY MAX-SHARPE (correlation-aware), shrinkage grid")
print("  d = shrink toward diagonal; w_max = 2.0x equal-weight cap\n")
rows = []
for d in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7):
    Sig_d = (1 - d) * Sig.values + d * np.diag(np.diag(Sig.values))
    w = max_sharpe(mu.values, Sig_d)
    relw_opt = pd.Series(0.0, index=NAMES)
    relw_opt[IS_HAVE] = w
    relw_opt = relw_opt / relw_opt.sum() * relw_heur.sum()    # same total scale as heuristic
    net_o, _, to_o = build_net(relw_opt)
    m_is = metrics(net_o.loc[:IS_END - pd.Timedelta(days=1)], f"   opt d={d:.1f}  IS")
    m_oos = metrics(net_o.loc[IS_END:], f"   opt d={d:.1f}  OOS")
    m_full = metrics(net_o, f"   opt d={d:.1f}  FULL")
    show(m_is, f"| IS-SR-fit={float(w@mu.values/np.sqrt(w@Sig.values@w)):.3f}")
    show(m_oos); show(m_full)
    rows.append(dict(d=d, is_sr=m_is['sr'], oos_sr=m_oos['sr'], full_sr=m_full['sr'],
                     full_ann=m_full['ann'], full_mdd=m_full['mdd'], neg=m_full['neg'],
                     to=float(to_o.mean() * 252 * BPS), w=w))
    print()

print("=" * 118)
print("weight comparison — heuristic share vs d=0.2 optimiser share")
Sig_d = 0.8 * Sig.values + 0.2 * np.diag(np.diag(Sig.values))
w02 = max_sharpe(mu.values, Sig_d)
cmp = pd.DataFrame({"IS_SR": SR_is[IS_HAVE], "heur_share": (relw_heur[IS_HAVE] / relw_heur.sum()),
                    "opt_share_d02": w02}).sort_values("heur_share", ascending=False)
cmp["delta"] = cmp.opt_share_d02 - cmp.heur_share
print(cmp.to_string(float_format=lambda x: f"{x:+.4f}"))
