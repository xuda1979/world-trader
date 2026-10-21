"""TASK 2/3 v2: inverse engine-spec solver at capital-real 1.6x, honest financing, WITH budget fill.
old block = REAL V3 BAL capped @1.6x+4.5% path (mu 15.8%/yr arith, vol 4.35%, SR 3.63, gross mean 1.527).
new engines: N iid, net SR s, instr vol 10% (charter convention), long/flat gross 1.0 (g param).
Mix gross_t = (1-W)*gross_old_t + W*g. Static re-gear k = 1.6/P99(gross_mix), then DAY-LEVEL cap
kappa_t = min(1, 1.6/(k*gross_mix_t)) (never breaches 1.6), margin on (kappa*k*gross_mix_t - 1)+.
Gaussian tails for engines = OPTIMISTIC (disclosed); t4 robustness on the frontier point.
"""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L

rng = np.random.default_rng(7)
rA, gA, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
rB, gB, _ = L.capped_book(L.NEW3, 0.091, 0.03, rate=0.045)
old = (((rA+rB)/2).dropna()); old = old[old.index >= '2008-03-31']
gross_old = (((gA+gB)/2).reindex(old.index)).dropna()
n = len(old); mu_old = old.mean(); sd_old = old.std()
RATE = 0.045

def mix_stats(N, s, g, W, seeds=200, tail='gauss'):
    gross_mix = (1-W)*gross_old.values + W*g
    k = 1.6/np.quantile(gross_mix, 0.99)
    kap = np.minimum(1.0, 1.6/np.maximum(k*gross_mix, 1e-9))
    G = k*kap*gross_mix
    margin_d = np.clip(G-1, 0, None)*RATE/252
    sig = min(0.10, 0.16/g)
    mu_e, sd_e = s*sig/252, sig/np.sqrt(252)
    if tail == 't4':
        z = rng.standard_t(4, size=(seeds, N, n))/np.sqrt(4/2); z = (z-z.mean())/z.std()
    olds = old.values
    # closed-form SR (scale-invariant) & ann on the mean path
    mu_c = (1-W)*mu_old + W*mu_e; sd_c = np.sqrt((1-W)**2*sd_old**2 + W**2*sd_e**2/N)
    kap_eff = np.mean(kap*k)
    SR = mu_c/sd_c*np.sqrt(252)
    ann = (mu_c*np.mean(kap*k) - margin_d.mean())*252
    vol = sd_c*np.mean(kap*k)*np.sqrt(252)
    # sim for MDD (fat-tail option on engines only)
    mdds = np.empty(seeds)
    for i in range(seeds):
        if tail == 't4':
            E = rng.standard_t(4, size=(N, n)); E = (E-E.mean())/E.std()*sd_e + mu_e
        else:
            E = rng.normal(mu_e, sd_e, size=(N, n))
        newblk = E.mean(axis=0)
        r = ((1-W)*olds + W*newblk)*(kap*k) - margin_d
        eq = np.cumprod(1+r); pk = np.maximum.accumulate(eq)
        mdds[i] = ((eq/pk)-1).min()
    return dict(SR=SR, ann=ann*100, vol=vol*100, mdd_mean=mdds.mean()*100, mdd_p95=np.percentile(mdds,5)*100,
                gross=G.mean())

print("=== TASK 2 TABLE (budget-fill enabled): best W by ann s.t. MDD_p95>=-7; N engines SR s, vol10%, gross g ===")
print(f"{'N':>3} {'s':>4} {'g':>4} {'W*':>4} | {'SR':>6} {'ann%':>6} {'vol%':>5} {'gross':>6} | {'MDDmean':>7} {'MDDp95':>7} | 80? 5? 7?")
for N in (4, 6, 8, 10):
    for s in (1.0, 1.5, 2.0):
        rows = []
        for g in (1.0, 2.5):
            for W in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
                d = mix_stats(N, s, g, W, seeds=120)
                rows.append((g, W, d))
        ok = [r for r in rows if r[2]['mdd_p95'] >= -7.0]
        pick = max(ok if ok else rows, key=lambda r: r[2]['ann'])
        g, W, d = pick
        print(f"{N:>3} {s:>4.1f} {g:>4.1f} {W:>4.1f} | {d['SR']:>6.2f} {d['ann']:>6.1f} {d['vol']:>5.1f} {d['gross']:>6.3f} | {d['mdd_mean']:>7.2f} {d['mdd_p95']:>7.2f} | {'YES' if d['ann']>=80 else 'no ':^3} {'YES' if d['SR']>=5 else 'no ':^3} {'YES' if d['mdd_p95']>=-7 else 'no':^3}")

print("\n=== TASK 3: per-engine SR s* (ann>=80, SR>=5, MDDp95<=7), all-new book W=1 ===")
from scipy.optimize import brentq
for N in (4, 6, 8, 10, 16, 25):
    for g in (1.0,):
        def f(s):
            d = mix_stats(N, s, g, 1.0, seeds=60)
            if d['mdd_p95'] < -7.0: return -1.0
            return min(d['ann']-80.0, (d['SR']-5.0)*10.0)
        lo, hi = 0.5, 10.0
        if f(lo) > 0: sstar = lo
        elif f(hi) < 0: sstar = float('nan')
        else: sstar = brentq(f, lo, hi, xtol=0.01)
        txt = f"{sstar:.2f}" if sstar == sstar else ">10 INFEASIBLE"
        if sstar == sstar:
            d = mix_stats(N, sstar, g, 1.0, seeds=200, tail='t4')
            t4 = f" | t4-fat-tail: SR {d['SR']:.2f} ann {d['ann']:.1f}% MDDp95 {d['mdd_p95']:.2f}%"
        else: t4 = ""
        print(f"N={N:>2} g={g:>3.1f} long/flat: s* = {txt}{t4}")

print("\n=== LAW (10%-vol instruments, gross 1.0, fill to 1.6x, margin 4.5%): ===")
print("vol_book fixed 16%; need SR_book >= (80+2.7)/16 = 5.17; SR_book = s*sqrt(N) -> s*_min(N):")
for N in (1, 4, 6, 8, 10, 16, 25):
    print(f"  N={N:>2}: per-engine net SR >= {5.17/np.sqrt(N):.2f}")
print("DD law (Gaussian p95, ln20): MDD_p95 ~ 3.0*vol/(2*SR) -> at vol16 SR5.17: "
      f"{3.0*16/(2*5.17):.2f}% (<=7 PASS)")
