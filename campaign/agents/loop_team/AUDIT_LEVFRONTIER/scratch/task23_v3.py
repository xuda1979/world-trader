"""TASK 2/3 v3 — corrected conventions (geo ann, MDD sim, per-engine instrument vol).
Construction matches honest13: K engines EW (slot avg) -> global fill to 1.6x gross.
  mu_net_ann = 1.6*v*s - margin(2.7) [arith];  sigma_book = 1.6*v/sqrt(K);
  SR_gross = s*sqrt(K); SR_net = (s - 0.027/(1.6*v))*sqrt(K);
  ann_geo = exp(mu_net - sigma^2/2) - 1  [identity verified -0.005pp on real path]
  MDD: 300-seed Gaussian sim (no throttle = conservative), p95 (5th pct).
Bar: ann_geo>=80, SR_net>=5, MDD_p95>=-7.  Solver on s for K in {1,4,6,8,10}, v in {.08,.10,.15,.20}.
"""
import numpy as np
from scipy.optimize import brentq
rng = np.random.default_rng(23)
RATE = 0.045; CAPG = 1.6; T = 4713

def mdd_p95(K, s, v, seeds=300):
    sig = CAPG*v/np.sqrt(K)
    mu = (CAPG*v*s - CAPG*RATE*(CAPG-1)/CAPG)/252  # per-day: fill gross 1.6 -> margin 0.6*rate
    margin_d = (CAPG-1)*RATE/252
    mu_d = (CAPG*v*s)/252 - margin_d
    sd_d = sig/np.sqrt(252)
    out = np.empty(seeds)
    for i in range(seeds):
        r = rng.normal(mu_d, sd_d, T)
        eq = np.cumprod(1+r); pk = np.maximum.accumulate(eq)
        out[i] = ((eq/pk)-1).min()
    return out.mean()*100, np.percentile(out,5)*100

def eval_point(K, s, v, seeds=300):
    sig = CAPG*v/np.sqrt(K)
    mu_net = CAPG*v*s - (CAPG-1)*RATE
    SR_net = (s - (CAPG-1)*RATE/(CAPG*v))*np.sqrt(K)
    ann_geo = (np.exp(mu_net - sig**2/2)-1)*100
    mm, p5 = mdd_p95(K, s, v, seeds)
    return dict(ann=ann_geo, SR=SR_net, sig=sig*100, mdd_mean=mm, mdd_p95=p5)

print("=== REQUIRED per-engine NET SR s* (ann_geo>=80 & SR_net>=5 & MDDp95>=-7) ===")
print(f"{'K':>3} {'v=8%':>8} {'v=10%':>8} {'v=15%':>8} {'v=20%':>8}")
for K in (1, 4, 6, 8, 10, 14):
    row = f"{K:>3}"
    for v in (0.08, 0.10, 0.15, 0.20):
        def f(s):
            d = eval_point(K, s, v, seeds=120)
            if d['mdd_p95'] < -7.0: return -1.0
            return min(d['ann']-80.0, (d['SR']-5.0)*10.0)
        lo, hi = 0.3, 30.0
        if f(lo) > 0: s = lo
        elif f(hi) < 0: s = float('nan')
        else: s = brentq(f, lo, hi, xtol=0.01)
        row += f" {'INFEAS' if s!=s else f'{s:7.2f}':>8}"
    print(row)

print("\n=== REALITY CHECK: what N engines of SR s DO deliver (v=10%, all-new, budget-filled) ===")
print(f"{'K':>3} {'s':>5} | {'SR_net':>6} {'ann_geo%':>8} {'vol%':>5} {'MDDmean':>7} {'MDDp95':>7}")
for (K, s) in [(4,1.0),(4,1.5),(4,2.0),(6,2.0),(10,2.0),(10,2.5),(4,3.0),(10,3.0),(4,5.2),(1,5.2),(10,5.2)]:
    d = eval_point(K, s, 0.10, seeds=300)
    print(f"{K:>3} {s:>5.2f} | {d['SR']:>6.2f} {d['ann']:>8.1f} {d['sig']:>5.1f} {d['mdd_mean']:>7.2f} {d['mdd_p95']:>7.2f}")

print("\n=== LAW: ann_geo@1.6x = exp(1.6*v*s - 2.7% - drag) - 1  (v=10%: ~exp(0.16s-0.028)-1) ===")
for s in (1.0, 1.5, 1.91, 2.0, 2.5, 3.0, 4.0, 5.2):
    print(f"  s={s:4.2f}: ann_geo ~ {(np.exp(0.16*s-0.027-0.0128/10)-1)*100:6.1f}% (K=10)   best-hunt benchmark CFX4 s=1.91 -> {(np.exp(0.16*1.91-0.027-0.0128/10)-1)*100:.1f}%")
