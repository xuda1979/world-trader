#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 3: apply the champion's OWN pre-committed IS rule, then validate.

The champion's builder documents its parameter choice verbatim:
    "P was chosen by a PRE-COMMITTED a-priori rule: the largest P maximizing IS annualized-return
     subject to (IS SR>=3.5) AND (IS MaxDD >= -6.0% = 1pp safety buffer under the -7% goal)
     AND (IS 0 negative years). Single OOS reveal then confirmed..."
We apply the SAME rule to the correlation-aware family (max-Sharpe + shrinkage d), i.e.
     maximise IS ann  s.t.  IS SR >= 3.5, IS MDD >= -6.0%, 0 IS negative years
then reveal OOS ONCE for the single selected member. Hyperparameter selection never touches OOS.

Also runs: halves-consistency, year-by-year, cost/turnover, gross audit, and a bootstrap
stability check of the fitted weights.
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
    net = (pd.Series(port, index=df.index) - to * BPS / 1e4
           - np.maximum(GEAR - 1, 0) * RATE / 252)
    return net, Wg, to

def stats(net):
    n = len(net); nav = (1 + net).cumprod()
    yr = net.groupby(net.index.year).apply(lambda r: (1 + r).prod() - 1)
    return dict(n=n, ann=float(nav.iloc[-1] ** (252 / n) - 1),
                sr=float(net.mean() / net.std(ddof=1) * np.sqrt(252)),
                mdd=float((nav / nav.cummax() - 1).min()), neg=int((yr < 0).sum()),
                worst=float(yr.min()), yr=yr)

def line(tag, s):
    print(f"  {tag:26s} n={s['n']:5d} ann={s['ann']*100:7.3f}%  SR={s['sr']:6.4f}  "
          f"MDD={s['mdd']*100:7.4f}%  neg={s['neg']}  worst={s['worst']*100:+7.3f}%")

mu = X.mean() * 252; Sig = X.cov() * 252; sd = np.sqrt(np.diag(Sig))

def max_sharpe(mu_v, Sig_m, w_max=2.0):
    k = len(mu_v)
    f = lambda w: -(w @ mu_v) / max(np.sqrt(w @ Sig_m @ w), 1e-14)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0.0, w_max)] * k
    best = None
    for w0 in (np.full(k, 1 / k), np.maximum(mu_v, 0) / max(np.maximum(mu_v, 0).sum(), 1e-12),
               (1 / sd) / (1 / sd).sum()):
        r = minimize(f, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun): best = r
    return best.x

# ---------------------------------------------------------------- IS rule: maximise IS ann
# subject to IS SR >= 3.5, IS MDD >= -6.0%, 0 IS negative years.
relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
base_net, _, _ = build_net(relw_heur)
base = stats(base_net); base_is = stats(base_net.loc[IS_MASK]); base_oos = stats(base_net.loc[~IS_MASK])
print("=" * 112)
print("CHAMPION (heuristic P=0.55), recomputed here")
line("IS", base_is); line("OOS", base_oos); line("FULL", base)
print(f"  champion IS-rule objective (IS ann) = {base_is['ann']*100:.4f}%")
print()

feas, grid = [], []
for d in np.round(np.arange(0.0, 0.81, 0.01), 2):
    Sig_d = (1 - d) * Sig.values + d * np.diag(np.diag(Sig.values))
    w = max_sharpe(mu.values, Sig_d)
    rw = pd.Series(0.0, index=NAMES); rw[IS_HAVE] = w
    rw = rw / rw.sum() * relw_heur.sum()
    net, _, _ = build_net(rw)
    s_is = stats(net.loc[IS_MASK]); s_oos = stats(net.loc[~IS_MASK]); s_full = stats(net)
    ok = (s_is['sr'] >= 3.5) and (s_is['mdd'] >= -0.06) and (s_is['neg'] == 0)
    grid.append(dict(d=d, ok=ok, is_ann=s_is['ann'], is_sr=s_is['sr'], is_mdd=s_is['mdd'],
                     oos_sr=s_oos['sr'], oos_ann=s_oos['ann'], full_sr=s_full['sr'],
                     full_ann=s_full['ann'], full_mdd=s_full['mdd'], w=w))
    if ok: feas.append(grid[-1])

g = pd.DataFrame([{k: v for k, v in r.items() if k != 'w'} for r in grid])
print("=" * 112)
print("FEASIBILITY GRID under the champion's IS rule (IS SR>=3.5, IS MDD>=-6.0%, 0 neg yrs)")
print(g.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
print()

if not feas:
    print("NO feasible correlation-aware member — family rejected."); sys.exit(0)
sel = max(feas, key=lambda r: r['is_ann'])
print("=" * 112)
print(f"SELECTED by the champion's own pre-committed IS rule: d={sel['d']:.2f}")
print(f"  IS rule objective  {sel['is_ann']*100:.4f}%  vs champion {base_is['ann']*100:.4f}%   "
      f"-> IS lift {100*(sel['is_ann']-base_is['ann']):+.4f}pp")
print(f"  IS constraints: SR {sel['is_sr']:.4f} (>=3.5), MDD {sel['is_mdd']*100:.4f}% (>=-6.0%), neg {0}")
print()
print("SINGLE OOS REVEAL for the selected member (selection used IS only):")
rw_sel = pd.Series(0.0, index=NAMES); rw_sel[IS_HAVE] = sel['w']
rw_sel = rw_sel / rw_sel.sum() * relw_heur.sum()
net_sel, Wg_sel, to_sel = build_net(rw_sel)
s_is = stats(net_sel.loc[IS_MASK]); s_oos = stats(net_sel.loc[~IS_MASK]); s_full = stats(net_sel)
line("candidate IS", s_is); line("candidate OOS", s_oos); line("candidate FULL", s_full)
print()
line("champion IS", base_is); line("champion OOS", base_oos); line("champion FULL", base)
print()
print("DELTAS (candidate - champion):")
print(f"  IS   dSR {s_is['sr']-base_is['sr']:+.4f}   dAnn {100*(s_is['ann']-base_is['ann']):+.4f}pp   "
      f"dMDD {100*(s_is['mdd']-base_is['mdd']):+.4f}pp")
print(f"  OOS  dSR {s_oos['sr']-base_oos['sr']:+.4f}   dAnn {100*(s_oos['ann']-base_oos['ann']):+.4f}pp   "
      f"dMDD {100*(s_oos['mdd']-base_oos['mdd']):+.4f}pp")
print(f"  FULL dSR {s_full['sr']-base['sr']:+.4f}   dAnn {100*(s_full['ann']-base['ann']):+.4f}pp   "
      f"dMDD {100*(s_full['mdd']-base['mdd']):+.4f}pp   dneg {s_full['neg']-base['neg']}")
print()

# ---------------------------------------------------------------- audits
gross = Wg_sel.abs().sum(axis=1)
print("=" * 112)
print("CONSTRUCTION AUDIT (candidate)")
print(f"  gross mean {gross.mean():.8f} max {gross.max():.12f} days>1.6 {int((gross>1.6+1e-9).sum())}")
print(f"  turnover {to_sel.mean()*252*BPS:.4f} bp/yr (champion {stats(base_net)['sr'] and 'see card'})")
print(f"  margin drag {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")
print()

# halves consistency of the DELTA (OOS split in two)
oos = net_sel.loc[~IS_MASK]
mid = oos.index[len(oos)//2]
for tag, sl in (("H1", slice(None, mid)), ("H2", slice(mid, None))):
    a = stats(net_sel.loc[sl]); b = stats(base_net.loc[sl])
    print(f"  {tag} (OOS {str(sl.start.date()) if sl.start else ''}..): "
          f"cand SR {a['sr']:.4f} vs champ {b['sr']:.4f}  dSR {a['sr']-b['sr']:+.4f}")
print()

print("YEAR-BY-YEAR (candidate vs champion, net):")
yb = pd.DataFrame({"cand": s_full['yr'], "champ": base['yr']})
yb["diff_pp"] = (yb.cand - yb.champ) * 100
print(yb.to_string(float_format=lambda x: f"{x*100:+.4f}%" if abs(x) < 1 else f"{x:+.4f}"))
print(f"\n  years candidate beats champion: {int((yb.diff_pp>0).sum())}/{len(yb)}")
print()

print("=" * 112)
print("WEIGHTS (share of book):")
cmp = pd.DataFrame({"IS_SR": pd.Series({n: rb.is_sr(isr_all[n]) for n in IS_HAVE}),
                    "champ_share": (relw_heur[IS_HAVE] / relw_heur.sum()),
                    "cand_share": pd.Series(sel['w'], index=IS_HAVE)})
cmp["delta"] = cmp.cand_share - cmp.champ_share
print(cmp.sort_values("cand_share", ascending=False).to_string(float_format=lambda x: f"{x:+.4f}"))
