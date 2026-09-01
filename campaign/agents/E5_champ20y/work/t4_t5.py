import numpy as np, pandas as pd, json
from e5lib import *

rA, _, _ = construct20(0.065, 0.04)
rB, _, _ = construct20(0.08, 0.03)
BAL = ((rA + rB) / 2).dropna()

print("=" * 90)
print("TASK 4: BLOCK BOOTSTRAP (1000x, 21-day blocks, seed=7)")
print("=" * 90)
def block_boot(r, n=1000, blk=21, seed=7):
    rng = np.random.default_rng(seed)
    x = r.values; N = len(x)
    sr = np.empty(n); ann = np.empty(n); mdd = np.empty(n)
    for i in range(n):
        idx = []
        while len(idx) < N:
            st = rng.integers(0, N - blk)
            idx.extend(range(st, st + blk))
        xb = x[idx[:N]]
        mu, sd = xb.mean(), xb.std()
        sr[i] = mu / sd * np.sqrt(252)
        ann[i] = (1 + mu) ** 252 - 1
        eq = np.cumprod(1 + xb); mdd[i] = (eq / np.maximum.accumulate(eq) - 1).min()
    return sr, ann, mdd

out = {}
for name, r in [("SAFE", rA), ("BALANCED", BAL), ("AGGRESSIVE", rB)]:
    sr, an, md = block_boot(r)
    lo, hi = np.percentile(sr, [2.5, 97.5]); alo, ahi = np.percentile(an * 100, [2.5, 97.5])
    real_sr = r.mean() / r.std() * np.sqrt(252)
    out[name] = dict(sr_lo=lo, sr_hi=hi, ann_lo=alo, ann_hi=ahi,
                     p_sr_lt2=float((sr < 2).mean()), p_ann_lt25=float((an < 0.25).mean()),
                     mdd_p5=float(np.percentile(md, 5) * 100))
    print(f"{name:10s} SR 95%CI [{lo:.2f}, {hi:.2f}]  real={real_sr:.2f}  P(SR<2)={out[name]['p_sr_lt2']:.3f}")
    print(f"{'':10s} ann 95%CI [{alo:.1f}%, {ahi:.1f}%]  P(ann<25%)={out[name]['p_ann_lt25']:.3f}  bootDD p5={out[name]['mdd_p5']:.1f}%")
json.dump(out, open("/Users/daxu/software/world-trader/campaign/agents/E5_champ20y/work/t4_boot.json", "w"), indent=1)

print()
print("=" * 90)
print("TASK 5: POSITION-PERmutation SCRAMBLE on the blend (200x, D2-documented method)")
print("=" * 90)
u, tw = _pool_norm()
def scramble_test(TGT, THR, n=200, seed=11):
    r_real, s, uu = construct20(TGT, THR)
    rng = np.random.default_rng(seed)
    sv = s.values; uv = u.reindex(r_real.index).values
    twv = tw.reindex(r_real.index).values
    COST = 6 / 1e4
    real = r_real.mean() / r_real.std() * np.sqrt(252)
    cnt = 0
    for _ in range(n):
        p = rng.permutation(len(sv))
        sp = sv[p]
        gross = uv * sp
        # re-apply trailing vol target honestly (only past data)
        vol = pd.Series(gross).rolling(60).std().shift(1).values * np.sqrt(252)
        scale = np.clip(0.08 / vol, 0, 8); scale[np.isnan(scale)] = 0
        g2 = gross * scale
        dsc = pd.Series(sp).diff().abs().values * 0.5
        net = g2 - (twv + np.nan_to_num(dsc)) * COST
        net = net[~np.isnan(net)]
        srs = net.mean() / net.std() * np.sqrt(252)
        if srs >= real: cnt += 1
    return cnt / n, real

for name, (t, h) in [("SAFE", (0.065, 0.04)), ("AGGRESSIVE", (0.08, 0.03))]:
    p, real = scramble_test(t, h)
    print(f"{name:10s} real SR={real:.2f}  scramble p={p:.4f}  ({'PASS' if p <= 0.05 else 'FAIL'})")
rA2, _, _ = construct20(0.065, 0.04); rB2, _, _ = construct20(0.08, 0.03)
BAL2 = ((rA2 + rB2) / 2).dropna()
real_b = BAL2.mean() / BAL2.std() * np.sqrt(252)
rng = np.random.default_rng(11)
# BALANCED scramble: average of the two scrambled series per permutation
svA = construct20(0.065, 0.04)[1].values; svB = construct20(0.08, 0.03)[1].values
uv = u.reindex(BAL2.index).values; twv = tw.reindex(BAL2.index).values; COST = 6 / 1e4
cnt = 0; N = 200
for _ in range(N):
    pA = rng.permutation(len(svA)); pB = rng.permutation(len(svB))
    def one(sv, pv):
        sp = sv[pv]; gross = uv * sp
        vol = pd.Series(gross).rolling(60).std().shift(1).values * np.sqrt(252)
        scale = np.clip(0.08 / vol, 0, 8); scale[np.isnan(scale)] = 0
        dsc = pd.Series(sp).diff().abs().values * 0.5
        return gross * scale - (twv + np.nan_to_num(dsc)) * COST
    nb = (one(svA, pA) + one(svB, pB)) / 2
    nb = nb[~np.isnan(nb)]
    if nb.mean() / nb.std() * np.sqrt(252) >= real_b: cnt += 1
print(f"{'BALANCED':10s} real SR={real_b:.2f}  scramble p={cnt/N:.4f}  ({'PASS' if cnt/N <= 0.05 else 'FAIL'})")
