"""CHARTER TASK 2 TABLE (corrected conventions): new engines ADDED to existing champion pool.
old = V3 BAL @1.6x+4.5% margin real path (ann_geo 16.99, vol 4.35, SR 3.628, gross mean 1.527).
new: K iid engines SR s, instr vol 10%, long/flat gross 1.0, corr 0 (all).
mix gross = (1-W)*gross_old_t + W*1.0; fill k = 1.6/p99; day-cap; margin 4.5% on (G-1)+.
ann_geo measured per seed (geo, not arith); 150 seeds; report median seed.
"""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L

rng = np.random.default_rng(31)
rA, gA, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
rB, gB, _ = L.capped_book(L.NEW3, 0.091, 0.03, rate=0.045)
old = ((rA+rB)/2).dropna(); old = old[old.index >= '2008-03-31']
gross_old = ((gA+gB)/2).reindex(old.index).dropna().values
olds = old.values; n = len(olds)
RATE = 0.045

def run(K, s, W, v=0.10, seeds=150):
    gross_mix = (1-W)*gross_old + W*1.0
    k = 1.6/np.quantile(gross_mix, 0.99)
    kap = np.minimum(1.0, 1.6/np.maximum(k*gross_mix, 1e-9))
    G = k*kap*gross_mix
    margin_d = np.clip(G-1, 0, None)*RATE/252
    mu_e, sd_e = s*v/252, v/np.sqrt(252)
    anns = np.empty(seeds); mdds = np.empty(seeds); srs = np.empty(seeds)
    for i in range(seeds):
        E = rng.normal(mu_e, sd_e, size=(K, n))
        r = ((1-W)*olds + W*E.mean(axis=0))*(k*kap) - margin_d
        eq = np.cumprod(1+r); pk = np.maximum.accumulate(eq)
        mdds[i] = ((eq/pk)-1).min()
        anns[i] = ((1+r).prod()**(252/n)-1)
        srs[i] = r.mean()/r.std()*np.sqrt(252)
    return np.median(anns)*100, np.median(srs), np.median(mdds)*100, np.percentile(mdds,5)*100

print(f"old alone @1.6x+4.5%: ann_geo 16.99% SR 3.628 MDD -3.59% (measured)")
print(f"{'K':>3} {'s':>4} | {'W*: ann-max s.t. MDDp95>=-7':>28} | {'ann_geo%':>8} {'SR':>6} {'MDDmed':>7} {'MDDp95':>7}")
for K in (4, 6, 8, 10):
    for s in (1.0, 1.5, 2.0):
        best = None
        for W in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
            a, sr, mm, p5 = run(K, s, W)
            if p5 >= -7.0 and (best is None or a > best[1]):
                best = (W, a, sr, mm, p5)
        if best is None:  # MDD gate fails everywhere: take W minimizing damage
            res = [(run(K, s, W)[3], W, run(K, s, W)) for W in (0.2, 0.4, 0.6)]
            res.sort(); W, (a, sr, mm, p5) = res[0][1], res[0][2]
            print(f"{K:>3} {s:>4.1f} | {'(MDD gate FAILS all W)':>28} | {a:>8.1f} {sr:>6.2f} {mm:>7.2f} {p5:>7.2f}")
        else:
            W, a, sr, mm, p5 = best
            print(f"{K:>3} {s:>4.1f} | {W:>28.1f} | {a:>8.1f} {sr:>6.2f} {mm:>7.2f} {p5:>7.2f}")
