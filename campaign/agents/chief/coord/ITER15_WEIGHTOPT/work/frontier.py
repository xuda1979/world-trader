#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 4: robustness of the shrinkage family + a general MV frontier family.

(A) Print the full shrinkage-d feasibility grid: does EVERY member beat the champion OOS?
    (robustness of the improvement to the hyperparameter).
(B) Test a strictly more general family: the long-only mean-variance frontier
        max  w'mu - (lam/2) w'Sig w    s.t. w>=0, sum w=1, w<=cap
    which nests max-return (lam->0) through min-variance (lam->inf). The champion's literal
    objective ("maximise IS ann s.t. IS SR>=3.5, IS MDD>=-6%, 0 neg yrs") is applied to pick lam.
(C) Bootstrap: resample IS blocks, re-fit, look at the spread of the fitted weight vector.
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

df = pd.DataFrame({n: rb.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
isr_all = df[df.index < IS_END]
IS_HAVE = [n for n in NAMES if isr_all[n].notna().sum() > 0]
X = isr_all[IS_HAVE].dropna()
IS_MASK = df.index < IS_END

def build_net(relw_vec):
    relw = pd.Series(relw_vec, index=NAMES, dtype=float)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to * BPS / 1e4 - np.maximum(GEAR-1, 0)*RATE/252)
    return net, Wg, to

def stats(net):
    n = len(net); nav = (1 + net).cumprod()
    yr = net.groupby(net.index.year).apply(lambda r: (1 + r).prod() - 1)
    return dict(n=n, ann=float(nav.iloc[-1] ** (252/n) - 1),
                sr=float(net.mean()/net.std(ddof=1)*np.sqrt(252)),
                mdd=float((nav/nav.cummax()-1).min()), neg=int((yr<0).sum()),
                worst=float(yr.min()))

relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
base_net, _, _ = build_net(relw_heur)
b_is, b_oos, b_full = stats(base_net.loc[IS_MASK]), stats(base_net.loc[~IS_MASK]), stats(base_net)
print(f"champion: IS SR {b_is['sr']:.4f} ann {b_is['ann']*100:.4f}% mdd {b_is['mdd']*100:.4f}% | "
      f"OOS SR {b_oos['sr']:.4f} | FULL SR {b_full['sr']:.4f} ann {b_full['ann']*100:.4f}%")
print()

mu = X.mean()*252; Sig = X.cov()*252; sd = np.sqrt(np.diag(Sig))

def max_sharpe(mu_v, Sig_m, w_max=2.0):
    k = len(mu_v)
    f = lambda w: -(w @ mu_v)/max(np.sqrt(w @ Sig_m @ w), 1e-14)
    cons = [{"type": "eq", "fun": lambda w: w.sum()-1.0}]; bnds = [(0.0, w_max)]*k
    best = None
    for w0 in (np.full(k, 1/k), np.maximum(mu_v,0)/max(np.maximum(mu_v,0).sum(),1e-12),
               (1/sd)/(1/sd).sum()):
        r = minimize(f, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun): best = r
    return best.x

def eval_w(w):
    rw = pd.Series(0.0, index=NAMES); rw[IS_HAVE] = w
    rw = rw / rw.sum() * relw_heur.sum()
    net, _, to = build_net(rw)
    return stats(net.loc[IS_MASK]), stats(net.loc[~IS_MASK]), stats(net), float(to.mean()*252*BPS)

rule_ok = lambda s: s['sr'] >= 3.5 and s['mdd'] >= -0.06 and s['neg'] == 0

# ---------------- (A) full shrinkage grid
print("=" * 118)
print("(A) SHRINKAGE FAMILY — full grid, ranked by IS-rule objective among feasible members")
rows = []
for d in np.round(np.arange(0.0, 0.82, 0.01), 2):
    Sig_d = (1-d)*Sig.values + d*np.diag(np.diag(Sig.values))
    w = max_sharpe(mu.values, Sig_d)
    s_is, s_oos, s_full, tv = eval_w(w)
    rows.append(dict(d=d, feas=rule_ok(s_is), is_ann=s_is['ann'], is_sr=s_is['sr'], is_mdd=s_is['mdd'],
                     oos_sr=s_oos['sr'], oos_ann=s_oos['ann'], full_sr=s_full['sr'],
                     full_ann=s_full['ann'], full_mdd=s_full['mdd'], turn=tv, w=w))
G = pd.DataFrame([{k: v for k, v in r.items() if k != 'w'} for r in rows])
F = G[G.feas]
print(f"feasible members: {len(F)}/{len(G)}   "
      f"IS-rule winner d={F.loc[F.is_ann.idxmax(),'d']:.2f}")
print(f"  OOS SR across ALL feasible members: min {F.oos_sr.min():.4f}  max {F.oos_sr.max():.4f}  "
      f"(champion OOS SR {b_oos['sr']:.4f})")
print(f"  members beating champion OOS SR: {int((F.oos_sr > b_oos['sr']).sum())}/{len(F)}")
print(f"  FULL SR across ALL members: min {G.full_sr.min():.4f} max {G.full_sr.max():.4f} "
      f"(champion {b_full['sr']:.4f});  FULL ann: min {G.full_ann.min()*100:.3f}% max {G.full_ann.max()*100:.3f}% "
      f"(champion {b_full['ann']*100:.3f}%)")
print(f"  members beating champion FULL ann: {int((G.full_ann > b_full['ann']).sum())}/{len(G)}")
print()

# ---------------- (B) general MV frontier family
print("=" * 118)
print("(B) GENERAL MV FRONTIER  max w'mu-(lam/2)w'Sig w   s.t. w>=0, sum=1, w<=0.25")
CAP = 0.25
def mv_w(lam):
    k = len(mu.values)
    f = lambda w: -(w @ mu.values) + 0.5*lam*(w @ Sig.values @ w)
    cons = [{"type": "eq", "fun": lambda w: w.sum()-1.0}]; bnds = [(0.0, CAP)]*k
    best = None
    for w0 in (np.full(k,1/k), np.maximum(mu.values,0)/max(np.maximum(mu.values,0).sum(),1e-12)):
        r = minimize(f, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 1200, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun): best = r
    return best.x

rowsb = []
for lam in list(np.round(np.arange(0.0, 10.01, 0.25), 2)) + [14, 18, 25, 40, 80]:
    w = mv_w(lam); s_is, s_oos, s_full, tv = eval_w(w)
    rowsb.append(dict(lam=lam, feas=rule_ok(s_is), is_ann=s_is['ann'], is_sr=s_is['sr'], is_mdd=s_is['mdd'],
                      oos_sr=s_oos['sr'], oos_ann=s_oos['ann'], full_sr=s_full['sr'],
                      full_ann=s_full['ann'], full_mdd=s_full['mdd'], turn=tv, w=w))
B = pd.DataFrame([{k: v for k, v in r.items() if k != 'w'} for r in rowsb])
Fb = B[B.feas]
if len(Fb):
    best_b = Fb.loc[Fb.is_ann.idxmax()]
    print(f"feasible {len(Fb)}/{len(B)}; IS-rule winner lam={best_b.lam:.2f}  "
          f"IS ann {best_b.is_ann*100:.4f}% SR {best_b.is_sr:.4f} MDD {best_b.is_mdd*100:.4f}%")
    print(f"  its OOS SR {best_b.oos_sr:.4f}  FULL SR {best_b.full_sr:.4f} ann {best_b.full_ann*100:.4f}% "
          f"MDD {best_b.full_mdd*100:.4f}%  turn {best_b.turn:.4f}bp/yr")
    print(f"  vs champion: OOS dSR {best_b.oos_sr-b_oos['sr']:+.4f} | FULL dSR {best_b.full_sr-b_full['sr']:+.4f} "
          f"dAnn {100*(best_b.full_ann-b_full['ann']):+.4f}pp")
else:
    print("no feasible MV member")
print()
print("MV frontier detail (every 4th rung):")
print(B.iloc[::4].to_string(index=False, float_format=lambda x: f"{x:.4f}"))

# ---------------- (C) bootstrap stability of the winner weights
print()
print("=" * 118)
print("(C) BLOCK-BOOTSTRAP stability of the shrinkage-family winner (21-day blocks, 200 resamples)")
rng = np.random.default_rng(20260911)
BOOT = 200; BLK = 21
Xv = X.values; T = len(Xv)
nb = int(np.ceil(T / BLK))
wins = []
for _ in range(BOOT):
    starts = rng.integers(0, T - BLK + 1, nb)
    idx = np.concatenate([np.arange(s, s+BLK) for s in starts])[:T]
    Xb = Xv[idx]
    mub = Xb.mean(axis=0)*252; Sb = np.cov(Xb, rowvar=False)*252
    Sbd = 0.38*Sb + 0.62*np.diag(np.diag(Sb))          # d=0.62
    wins.append(max_sharpe(mub, Sbd))
W = pd.DataFrame(wins, columns=IS_HAVE)
print("bootstrap weight distribution (share):")
print(pd.DataFrame({"mean": W.mean(), "p05": W.quantile(.05), "p95": W.quantile(.95),
                    "fitted_d062": pd.Series(G[G.d == 0.62].iloc[0]['w'] if False else
                                             next(r['w'] for r in rows if abs(r['d']-0.62) < 1e-9),
                                             index=IS_HAVE)})
      .to_string(float_format=lambda x: f"{x:+.4f}"))
print(f"\n  share of resamples where brwt-block weight < champion's 0.4687: "
      f"{np.mean([w[[IS_HAVE.index(n) for n in ['brwt5','brwt7','brwt10','brwt15']]].sum() < 0.4687 for w in wins]):.3f}")
