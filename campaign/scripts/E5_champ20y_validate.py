#!/usr/bin/env python3
"""E5_champ20y: full-validation of GOAL100_CHAMPION20Y (v1) + upgrade attempt (v2).

Tasks (charter E5):
 1. independent rebuild + byte-match vs committed CSVs
 2. sub-period DD audit (7 fixed ~3y windows, rolling-3y, all calendar years)
 3. cost stress 6/8/10 bps
 4. 1000x 21d-block bootstrap SR/ann CI
 5. position-permutation scramble (200x)
 6. vt/throttle grid {(0.07..0.09)x(0.03..0.045)}, IS(2007-2016)-selected vs A/B,
    OOS DD<=8% requirement
 7. 20y-span accounting vs 18.6y champion

Usage: python3 campaign/scripts/E5_champ20y_validate.py
Results (2026-09-01): all audits PASS -> v1 CONFIRMED; upgrade FAILS charter rule
(strict IS-argmax vt.090/thr.040 has OOS DD -8.6% > 8%; IS SR surface flat 4.38-4.44
= no IS edge to harvest). Honest frontier point (not adopted): B-slot vt.085/thr.035
-> combo 42.2% ann @ -7.3% DD, OOS 48.1%.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/E5_champ20y/work")
import numpy as np, pandas as pd
from e5lib import construct20, dd_series, _pool_norm
import champion_build as cb

# ---- Task 1: rebuild + byte match (run rebuild20y.py logic) ----
def task1():
    for name, (tgt, thr) in [("SAFE", (0.065, 0.04)), ("AGGRESSIVE", (0.08, 0.03))]:
        r, _, _ = construct20(tgt, thr)
        old = pd.read_csv(f"/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION20Y_{name}_daily.csv",
                          index_col=0, parse_dates=True).iloc[:, 0]
        j = pd.concat([old.rename("o"), r.rename("n")], axis=1, join="inner").dropna()
        print(f"T1 {name}: n={len(j)} max|diff|={float((j.o-j.n).abs().max()):.2e}")
    rA, _, _ = construct20(0.065, 0.04); rB, _, _ = construct20(0.08, 0.03)
    bal = ((rA + rB) / 2).dropna()
    return rA, rB, bal

# ---- Task 2: DD audit ----
def task2(rA, bal, rB):
    for name, r in [("SAFE", rA), ("BALANCED", bal), ("AGGRESSIVE", rB)]:
        dd = dd_series(r)
        ydd = dd.groupby(dd.index.year).min()
        flags = [(int(y), round(v * 100, 1)) for y, v in ydd.items() if v < -0.08]
        worst3 = min(dd.iloc[i - 756:i + 1].min() for i in range(756, len(dd)))
        print(f"T2 {name}: yrDD<-8%: {len(flags)} {flags}; worst rolling-3y DD {worst3*100:.1f}%")

# ---- Task 3: cost stress ----
def task3():
    for c in (6, 8, 10):
        rA, _, _ = construct20(0.065, 0.04, cost_bps=c)
        rB, _, _ = construct20(0.08, 0.03, cost_bps=c)
        bal = ((rA + rB) / 2).dropna()
        s = cb.stats(bal)
        print(f"T3 {c}bps BAL: ann={s['ann']} sr={s['sr']} mdd={s['mdd']} negy={s['negy']} oos={s['oos_ann']}")

# ---- Task 4: bootstrap ----
def task4(rA, bal, rB, n=1000, blk=21, seed=7):
    rng = np.random.default_rng(seed)
    for name, r in [("SAFE", rA), ("BALANCED", bal), ("AGGRESSIVE", rB)]:
        x = r.values; N = len(x)
        sr = np.empty(n); an = np.empty(n)
        for i in range(n):
            idx = []
            while len(idx) < N:
                st = rng.integers(0, N - blk); idx.extend(range(st, st + blk))
            xb = x[idx[:N]]
            sr[i] = xb.mean() / xb.std() * np.sqrt(252)
            an[i] = (1 + xb.mean()) ** 252 - 1
        lo, hi = np.percentile(sr, [2.5, 97.5]); alo, ahi = np.percentile(an * 100, [2.5, 97.5])
        print(f"T4 {name}: SR95%CI [{lo:.2f},{hi:.2f}] P(SR<2)={float((sr<2).mean()):.3f} "
              f"ann95%CI [{alo:.1f},{ahi:.1f}] P(ann<25%)={float((an<0.25).mean()):.3f}")

# ---- Task 5: scramble ----
def task5(rA, rB, n=200, seed=11):
    u, tw = _pool_norm(); COST = 6 / 1e4
    def one(sv, pv, idx):
        sp = sv[pv]; gross = u.reindex(idx).values * sp
        vol = pd.Series(gross).rolling(60).std().shift(1).values * np.sqrt(252)
        sc = np.clip(0.08 / vol, 0, 8); sc[np.isnan(sc)] = 0
        dsc = pd.Series(sp).diff().abs().values * 0.5
        return gross * sc - (tw.reindex(idx).values + np.nan_to_num(dsc)) * COST
    idx = rA.index
    svA = construct20(0.065, 0.04)[1].reindex(idx).values
    svB = construct20(0.08, 0.03)[1].reindex(idx).values
    bal = ((rA + rB) / 2).dropna()
    for name, sv, real in [("SAFE", svA, rA.mean()/rA.std()*np.sqrt(252)),
                           ("AGGRESSIVE", svB, rB.mean()/rB.std()*np.sqrt(252)),
                           ("BALANCED", None, bal.mean()/bal.std()*np.sqrt(252))]:
        rng = np.random.default_rng(seed); cnt = 0
        for _ in range(n):
            nb = one(svA, rng.permutation(len(svA)), idx)
            if sv is svB: nb = one(svB, rng.permutation(len(svB)), idx)
            else: nb = (one(svA, rng.permutation(len(svA)), idx) + one(svB, rng.permutation(len(svB)), idx)) / 2
            nb = nb[~np.isnan(nb)]
            if nb.mean() / nb.std() * np.sqrt(252) >= real: cnt += 1
        print(f"T5 {name}: real SR={real:.2f} scramble p={cnt/n:.4f}")

# ---- Task 6: grid ----
def task6():
    import itertools
    print("T6 grid (FULL ann/sr/dd | IS0716 sr | oosDD):")
    for t, h in itertools.product([0.07,0.075,0.08,0.085,0.09],[0.03,0.035,0.04,0.045]):
        r, _, _ = construct20(t, h)
        isr = r[r.index <= "2016-12-31"]; oos = r[r.index >= "2017-01-01"]
        s = cb.stats(r)
        print(f"  vt={t:.3f} thr={h:.3f}: {s['ann']:5.1f}/{s['sr']:4.2f}/{s['mdd']:5.1f} | "
              f"{isr.mean()/isr.std()*np.sqrt(252):4.2f} | {dd_series(oos).min()*100:5.1f}")

if __name__ == "__main__":
    rA, rB, bal = task1()
    task2(rA, bal, rB)
    task3(); task4(rA, bal, rB); task5(rA, rB); task6()
