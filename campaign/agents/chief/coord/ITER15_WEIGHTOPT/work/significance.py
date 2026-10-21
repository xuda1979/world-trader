#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 5: is the improvement distinguishable from noise?

Tests on the daily return DIFFERENCE  d_t = candidate_t - champion_t:
  1. mean / Newey-West t-stat (autocorrelation-robust, lag = 10)
  2. block bootstrap (21-day blocks) of the SR difference, OOS and FULL
  3. concentration: how much of the total difference comes from the top-k days
  4. tail behaviour: worst-day / worst-month / skew comparison
All differences are same-calendar-day, same-gross, same-cost-convention books.
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
    return (pd.Series(port, index=df.index) - to*BPS/1e4
            - np.maximum(GEAR-1, 0)*RATE/252), Wg, to

def sr(r): return float(r.mean()/r.std(ddof=1)*np.sqrt(252))

mu = X.mean()*252; Sig = X.cov()*252; sd = np.sqrt(np.diag(Sig))
def max_sharpe(mu_v, Sig_m, w_max=2.0):
    k = len(mu_v)
    f = lambda w: -(w @ mu_v)/max(np.sqrt(w @ Sig_m @ w), 1e-14)
    cons = [{"type": "eq", "fun": lambda w: w.sum()-1.0}]; bnds = [(0.0, w_max)]*k
    best = None
    for w0 in (np.full(k,1/k), np.maximum(mu_v,0)/max(np.maximum(mu_v,0).sum(),1e-12), (1/sd)/(1/sd).sum()):
        r = minimize(f, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter":800, "ftol":1e-12})
        if r.success and (best is None or r.fun < best.fun): best = r
    return best.x

relw_heur = np.maximum(pd.Series({n: rb.is_sr(isr_all[n]) for n in NAMES}), 0.0) ** P
net_base, _, _ = build_net(relw_heur)

Sig_d = 0.38*Sig.values + 0.62*np.diag(np.diag(Sig.values))     # d = 0.62
w = max_sharpe(mu.values, Sig_d)
relw_cand = pd.Series(0.0, index=NAMES); relw_cand[IS_HAVE] = w
relw_cand = relw_cand / relw_cand.sum() * relw_heur.sum()
net_cand, Wg_c, to_c = build_net(relw_cand)

d_full = (net_cand - net_base).dropna()
d_oos = d_full[d_full.index >= IS_END]
print(f"champion FULL SR {sr(net_base):.4f} | candidate FULL SR {sr(net_cand):.4f} "
      f"(dSR {sr(net_cand)-sr(net_base):+.4f})")
print(f"champion OOS  SR {sr(net_base[~IS_MASK]):.4f} | candidate OOS  SR {sr(net_cand[~IS_MASK]):.4f} "
      f"(dSR {sr(net_cand[~IS_MASK])-sr(net_base[~IS_MASK]):+.4f})")
print()

# ---------------- 1. Newey-West t-stat on the difference
def nw_t(d, lag=10):
    x = d.values - d.values.mean(); T = len(x)
    g0 = (x @ x)/T
    s = g0
    for L in range(1, lag+1):
        gl = (x[L:] @ x[:-L])/T
        s += 2*(1 - L/(lag+1))*gl
    se = np.sqrt(max(s, 1e-30)/T)
    return d.mean()/se

print("(1) DIFFERENCE SERIES  d = candidate - champion")
for tag, d in (("FULL", d_full), ("OOS", d_oos)):
    t = nw_t(d)
    print(f"  {tag:4s} n={len(d):5d}  mean={d.mean()*1e4:+7.4f} bp/day  ann={d.mean()*252*100:+.4f}%  "
          f"sd={d.std(ddof=1)*1e4:6.2f}bp  NW(lag10) t={t:+.3f}  p(2-sided)~{2*(1-__import__('scipy.stats',fromlist=['norm']).norm.cdf(abs(t))):.4f}")
print()

# ---------------- 2. block bootstrap of the SR difference
def boot_dsr(netA, netB, BOOT=2000, BLK=21, seed=20260911):
    rng = np.random.default_rng(seed)
    rA = netA.values; rB = netB.values; T = len(rA)
    nb = int(np.ceil(T/BLK)); out = np.empty(BOOT)
    for i in range(BOOT):
        st = rng.integers(0, T-BLK+1, nb)
        idx = np.concatenate([np.arange(s, s+BLK) for s in st])[:T]
        a = rA[idx]; b = rB[idx]
        out[i] = sr(pd.Series(a)) - sr(pd.Series(b))
    return out

for tag, mA, mB in (("FULL", net_cand, net_base),
                    ("OOS", net_cand[~IS_MASK], net_base[~IS_MASK]),
                    ("IS", net_cand[IS_MASK], net_base[IS_MASK])):
    bs = boot_dsr(mA, mB, BOOT=1500)
    print(f"(2) {tag:4s} block-bootstrap dSR: mean {bs.mean():+.4f}  "
          f"90% CI [{np.quantile(bs,.05):+.4f}, {np.quantile(bs,.95):+.4f}]  "
          f"P(dSR>0)={np.mean(bs>0):.4f}")
print()

# ---------------- 3. concentration
print("(3) CONCENTRATION of the FULL-period difference")
tot = d_full.sum()
for k in (5, 10, 20, 50):
    top = d_full.abs().nlargest(k)
    print(f"  top-{k:2d} |d| days carry {d_full.loc[top.index].sum()/tot*100:6.1f}% of the net difference; "
          f"their |d| sum = {top.sum()*1e4:.2f}bp vs net {tot*1e4:.2f}bp")
for y in (2020, 2022):
    print(f"  ex-{y}: net difference {d_full[d_full.index.year != y].sum()*252/len(d_full[d_full.index.year != y])*100:+.4f}%/yr")
print()

# ---------------- 4. tails
print("(4) TAIL comparison (FULL period, net daily)")
for tag, n in (("champion", net_base), ("candidate", net_cand)):
    print(f"  {tag:9s} worst day {n.min()*100:+.4f}%  best day {n.max()*100:+.4f}%  "
          f"skew {n.skew():+.3f}  kurt {n.kurtosis():+.3f}")
mo_c = net_cand.resample('ME').apply(lambda r: (1+r).prod()-1)
mo_b = net_base.resample('ME').apply(lambda r: (1+r).prod()-1)
print(f"  worst month: champion {mo_b.min()*100:+.4f}%  candidate {mo_c.min()*100:+.4f}%")
print(f"  worst rolling-63d: champion {(net_base.rolling(63).apply(lambda r:(1+r).prod()-1)).min()*100:+.4f}%  "
      f"candidate {(net_cand.rolling(63).apply(lambda r:(1+r).prod()-1)).min()*100:+.4f}%")
print()
print(f"turnover: champion {to_c.mean()*252*BPS:.4f} bp/yr (recomputed both) "
      f"| champion {(build_net(relw_heur)[2].mean()*252*BPS):.4f} bp/yr")
print(f"candidate weights: {dict(zip(IS_HAVE, np.round(w,4)))}")
