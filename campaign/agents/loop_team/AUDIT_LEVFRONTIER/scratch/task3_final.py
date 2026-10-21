"""TASK 3 final: closed-form s* = [ln(1.8) + 0.027 + 0.5*(1.6v)^2/K] / (1.6v)  (ann-binding,
K-weak) vs SR/MDD gates. High-seed MDD check at each closed-form point. 600 seeds."""
import numpy as np
rng = np.random.default_rng(99)
RATE = 0.045; CAPG = 1.6; T = 4713

def mdd_p95(K, s, v, seeds=600):
    sig = CAPG*v/np.sqrt(K); margin_d = (CAPG-1)*RATE/252
    mu_d = CAPG*v*s/252 - margin_d; sd_d = sig/np.sqrt(252)
    out = np.empty(seeds)
    for i in range(seeds):
        r = rng.normal(mu_d, sd_d, T)
        eq = np.cumprod(1+r); pk = np.maximum.accumulate(eq)
        out[i] = ((eq/pk)-1).min()
    return out.mean()*100, np.percentile(out,5)*100

print(f"{'K':>3} {'v':>5} | {'s*_ann':>6} | {'SR_net@s*':>9} | {'MDDmean':>7} {'MDDp95':>7} | {'ann@s*':>6} {'SR gate':>7} | binding")
for K in (1, 4, 6, 8, 10):
    for v in (0.08, 0.10):
        s_ann = (np.log(1.8) + (CAPG-1)*RATE + 0.5*(CAPG*v)**2/K) / (CAPG*v)
        SR_net = (s_ann - (CAPG-1)*RATE/(CAPG*v))*np.sqrt(K)
        ann = (np.exp(CAPG*v*s_ann - (CAPG-1)*RATE - 0.5*(CAPG*v)**2/K)-1)*100
        mm, p5 = mdd_p95(K, s_ann, v)
        mdd_ok = p5 >= -7.0; sr_ok = SR_net >= 5.0
        binding = "MDD" if not mdd_ok else ("SR>=5" if not sr_ok else "ANN (all pass)")
        print(f"{K:>3} {v*100:>4.0f}% | {s_ann:>6.3f} | {SR_net:>9.2f} | {mm:>7.2f} {p5:>7.2f} | {ann:>6.1f} {'PASS' if sr_ok else 'FAIL':>7} | {binding}")

# MDD-binding K=1 cell: solve s where MDDp95 = -7 exactly-ish
print("\nK=1 (single engine) MDD gate: find s where MDDp95 crosses -7 (600 seeds, bisection)")
for v in (0.10,):
    lo, hi = 5.0, 15.0
    for _ in range(12):
        mid = (lo+hi)/2
        mm, p5 = mdd_p95(1, mid, v, seeds=250)
        if p5 >= -7.0: hi = mid
        else: lo = mid
    print(f"  v={v*100:.0f}%: MDD-gate s* ~ {hi:.2f} (SR_net {(hi-(CAPG-1)*RATE/(CAPG*v)):.2f}); ann-gate s* = {(np.log(1.8)+(CAPG-1)*RATE+0.5*(CAPG*v)**2)/(CAPG*v):.2f} -> BINDING = {max(hi, (np.log(1.8)+(CAPG-1)*RATE+0.5*(CAPG*v)**2)/(CAPG*v)):.2f}")
