#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 7: the NAV-drift mixer as a second family.

The champion's construction multiplies relw by a NAV-drift term
        w_i(t)  ∝  relw_i * nav_i(t-1)/mean_j nav_j(t-1)
i.e. a relative-strength tilt on top of the fitted weights. Constant-mix (rho=0) instead
holds w_i ∝ relw_i fixed. Parameterise the continuum
        w_i(t)  ∝  relw_i * [ (1-rho) + rho * nav_i(t-1)/mean_j nav_j(t-1) ]
so rho=1 is the CANONICAL champion construction and rho=0 is constant-mix.

Family selection uses the SAME pre-committed IS rule as the champion
(max IS ann s.t. IS SR>=3.5, IS MDD>=-6.0%, 0 IS neg years). OOS is reported after.
"""
import sys, json
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
sd = np.sqrt(np.diag((X.cov()*252).values))
NAVN = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
NAVN = NAVN.div(NAVN.mean(axis=1), axis=0)          # cross-sectionally normalised nav

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

def build_net(relw_vec, rho=1.0):
    r = pd.Series(relw_vec, index=NAMES, dtype=float)
    d2 = NAVN.mul(r, axis=1) if rho >= 1.0 else (1-rho)*pd.DataFrame(
        np.tile(r.values, (len(df),1)), index=df.index, columns=NAMES) + rho*NAVN.mul(r, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    return (pd.Series(port, index=df.index) - to*BPS/1e4 - np.maximum(GEAR-1,0)*RATE/252), Wg, to

def st(s):
    n=len(s); nav=(1+s).cumprod()
    yr=s.groupby(s.index.year).apply(lambda r:(1+r).prod()-1)
    return dict(ann=float((nav.iloc[-1]**(252/n)-1)*100),
                sr=float(s.mean()/s.std(ddof=1)*np.sqrt(252)),
                mdd=float((nav/nav.cummax()-1).min()*100), neg=int((yr<0).sum()))

mu = X.mean()*252; Sig = X.cov()*252
relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
base,_,_ = build_net(relw_heur, 1.0)
b_is, b_oos, b_full = st(base[IS_MASK]), st(base[~IS_MASK]), st(base)
print(f"champion: IS ann {b_is['ann']:.4f}% SR {b_is['sr']:.4f} MDD {b_is['mdd']:.4f}% | "
      f"OOS SR {b_oos['sr']:.4f} | FULL ann {b_full['ann']:.4f}% SR {b_full['sr']:.4f} MDD {b_full['mdd']:.4f}%")
print()
rule_ok = lambda s: s['sr']>=3.5 and s['mdd']>=-6.0 and s['neg']==0
print("(rho, d) grid — using max-Sharpe weights at shrinkage d, mixed at rho")
print(f"{'d':>5} {'rho':>5} {'feas':>6} {'IS_ann':>9} {'IS_sr':>7} {'IS_mdd':>9} {'OOS_sr':>8} {'FULL_ann':>9} {'FULL_sr':>8} {'FULL_mdd':>9}")
rows=[]
for d in (0.0, 0.2, 0.4, 0.5, 0.62, 0.7):
    Sd = (1-d)*Sig.values + d*np.diag(np.diag(Sig.values))
    w = max_sharpe(mu.values, Sd)
    rw = pd.Series(0.0, index=NAMES); rw[IS_HAVE] = w; rw = rw/rw.sum()*relw_heur.sum()
    for rho in (0.0, 0.25, 0.5, 0.75, 1.0):
        net,_,to = build_net(rw, rho)
        s_is, s_oos, s_full = st(net[IS_MASK]), st(net[~IS_MASK]), st(net)
        ok = rule_ok(s_is)
        rows.append(dict(d=d, rho=rho, feas=ok, is_ann=s_is['ann'], is_sr=s_is['sr'], is_mdd=s_is['mdd'],
                         oos_sr=s_oos['sr'], full_ann=s_full['ann'], full_sr=s_full['sr'],
                         full_mdd=s_full['mdd'], turn=float(to.mean()*252*BPS), w=w))
        print(f"{d:5.2f} {rho:5.2f} {str(ok):>6} {s_is['ann']:9.4f} {s_is['sr']:7.4f} {s_is['mdd']:9.4f} "
              f"{s_oos['sr']:8.4f} {s_full['ann']:9.4f} {s_full['sr']:8.4f} {s_full['mdd']:9.4f}")

R = pd.DataFrame([{k:v for k,v in r.items() if k!='w'} for r in rows])
F = R[R.feas]
print()
if len(F):
    win = F.loc[F.is_ann.idxmax()]
    print(f"IS-rule winner over the (d,rho) family: d={win.d:.2f} rho={win.rho:.2f}  "
          f"IS ann {win.is_ann:.4f}%")
    print(f"  FULL ann {win.full_ann:.4f}% SR {win.full_sr:.4f} MDD {win.full_mdd:.4f}%  OOS SR {win.oos_sr:.4f}")
    print(f"  vs champion: dAnn {win.full_ann-b_full['ann']:+.4f}pp  dSR {win.full_sr-b_full['sr']:+.4f}  "
          f"dMDD {win.full_mdd-b_full['mdd']:+.4f}pp")
    dom = R[(R.full_ann > b_full['ann']) & (R.full_sr > b_full['sr'])]
    print(f"\n  members DOMINATING the champion on BOTH ann and SR: {len(dom)}/{len(R)}")
    if len(dom):
        print(dom.sort_values('full_ann', ascending=False).to_string(index=False, float_format=lambda x:f"{x:.4f}"))
