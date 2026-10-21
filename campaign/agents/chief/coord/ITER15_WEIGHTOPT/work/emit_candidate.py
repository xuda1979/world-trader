#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — emit the correlation-aware candidate champion + weights.

Deterministic: no RNG anywhere. The weight vector is fitted on the IS window
(< 2017-01-01) by long-only max-Sharpe on the shrinkage-0.62 covariance, then the
canonical builder machinery is applied VERBATIM (NAV-drift x relw, row-normalised,
gross exactly 1.6, FULL |dW| @ 6.4bps one-side, margin 4.5%/yr on (GEAR-1)).

Outputs (candidate namespace, NEVER overwrites the champion of record):
  campaign/agents/chief/coord/ITER15_WEIGHTOPT/RAWEW16_IS_MINSHARPE_weights.csv
  campaign/agents/chief/coord/ITER15_WEIGHTOPT/RAWEW16_daily.csv
  campaign/agents/chief/coord/ITER15_WEIGHTOPT/emit_report.json
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
D = 0.62                                    # selected by the champion's own IS rule
W_MAX, SHRINK = 2.0, D

df = pd.DataFrame({n: rb.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
isr_all = df[df.index < IS_END]
IS_HAVE = [n for n in NAMES if isr_all[n].notna().sum() > 0]
X = isr_all[IS_HAVE].dropna()
mu = X.mean()*252; Sig = X.cov()*252; sd = np.sqrt(np.diag(Sig))

def max_sharpe(mu_v, Sig_m, w_max=W_MAX):
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

Sig_d = (1-SHRINK)*Sig.values + SHRINK*np.diag(np.diag(Sig.values))
w = max_sharpe(mu.values, Sig_d)
relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
relw = pd.Series(0.0, index=NAMES); relw[IS_HAVE] = w
relw = relw / relw.sum() * relw_heur.sum()

def build_net(relw_vec):
    r = pd.Series(relw_vec, index=NAMES, dtype=float)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(r, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (GEAR / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index) - to*BPS/1e4 - np.maximum(GEAR-1, 0)*RATE/252)
    return net, Wg, to

net, Wg, to = build_net(relw)
net_heur, _, _ = build_net(relw_heur)

def st(s):
    n = len(s); nav = (1+s).cumprod()
    yr = s.groupby(s.index.year).apply(lambda r: (1+r).prod()-1)
    return dict(n=n, ann_pct=float((nav.iloc[-1]**(252/n)-1)*100),
                sr=float(s.mean()/s.std(ddof=1)*np.sqrt(252)),
                mdd_pct=float((nav/nav.cummax()-1).min()*100),
                neg_years=int((yr<0).sum()), worst_year_pct=float(yr.min()*100))

net.to_frame("ret").to_csv(f"{OUT}/RAWEW16_daily.csv")
relw.to_frame("relw").to_csv(f"{OUT}/RAWEW16_IS_MINSHARPE_weights.csv")

gross = Wg.abs().sum(axis=1)
rep = {
  "candidate": "RAWEW16_IS_MINSHARPE",
  "method": f"long-only max-Sharpe on IS covariance shrunk {SHRINK:.2f} toward diagonal, "
            f"w_max={W_MAX}x equal-weight; selected by the champion's own pre-committed IS rule "
            f"(max IS ann s.t. IS SR>=3.5, IS MDD>=-6.0%, 0 IS neg years)",
  "is_window": [str(df.index[df.index < IS_END].min().date()),
                str(df.index[df.index < IS_END].max().date())],
  "weights_source": "IS only; no OOS information used to fit or select",
  "weights": {n: float(relw[n]) for n in NAMES},
  "checks": {
    "gross_mean": float(gross.mean()), "gross_max": float(gross.max()),
    "gross_days_over_1p6": int((gross > 1.6 + 1e-9).sum()),
    "turnover_bp_per_yr": float(to.mean()*252*BPS),
    "margin_pct_per_yr": float(np.maximum(GEAR-1, 0)*RATE*100),
    "day1_entry_charged_bp": float(to.iloc[0]*BPS),
  },
  "candidate_stats": {"IS": st(net[net.index < IS_END]), "OOS": st(net[net.index >= IS_END]),
                      "FULL": st(net)},
  "heuristic_champion_stats": {"IS": st(net_heur[net_heur.index < IS_END]),
                               "OOS": st(net_heur[net_heur.index >= IS_END]),
                               "FULL": st(net_heur)},
}
with open(f"{OUT}/emit_report.json", "w") as fh:
    json.dump(rep, fh, indent=2)

print(f"emitted {OUT}/RAWEW16_daily.csv  n={len(net)}")
print(f"emitted {OUT}/RAWEW16_IS_MINSHARPE_weights.csv")
print()
for k in ("IS", "OOS", "FULL"):
    c, h = rep["candidate_stats"][k], rep["heuristic_champion_stats"][k]
    print(f"{k:4s} cand ann {c['ann_pct']:.4f}% SR {c['sr']:.4f} MDD {c['mdd_pct']:.4f}% neg {c['neg_years']}"
          f"   | champ ann {h['ann_pct']:.4f}% SR {h['sr']:.4f} MDD {h['mdd_pct']:.4f}% neg {h['neg_years']}"
          f"   | dAnn {c['ann_pct']-h['ann_pct']:+.4f}pp dSR {c['sr']-h['sr']:+.4f} dMDD {c['mdd_pct']-h['mdd_pct']:+.4f}pp")
print()
print(f"gross max {gross.max():.12f} days>1.6 {int((gross>1.6+1e-9).sum())} | "
      f"turnover {to.mean()*252*BPS:.4f} bp/yr | margin {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")
print(f"weights: {json.dumps({k: round(v,6) for k,v in rep['weights'].items()})}")
