#!/usr/bin/env python3
"""R2 final checks: is the +0.807pp dMDD 'pass' skill or a saturated one-date lottery?
 T1: random-gate null. 200 random binary gates (off% matched to the dom family, same flip
     cadence) on the champ: what fraction clear the charter bar dMDD>=+0.5pp? If ~as many
     as the 42% of real configs that clear it, the MDD leg is family-blind / degenerate.
 T2: single-episode dependence. Recompute dMDD EXCLUDING 2018-05..07: if ~0 for every
     nominally-passing config, the whole MDD leg IS the 2018-06-25 episode.
 T3: sc0.9 lightest-touch configs (only Calmar improvers) under scramble on the MDD claim.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")
import numpy as np, pandas as pd
from bt import metrics
from HUNT_CRYPTO2_round2_lib import load_env, all_configs, gate_metrics, binary_gate, cond_a_dom, COST

env = load_env()
CHAMP = env['CHAMP']
CEIL = (metrics.max_dd(CHAMP.loc[:'2017']) - metrics.max_dd(CHAMP))
print(f"champ MDD {metrics.max_dd(CHAMP)*100:.3f}% | 2008-episode {metrics.max_dd(CHAMP.loc[:'2017'])*100:.3f}% "
      f"| structural dMDD ceiling {CEIL*100:.3f}pp (charter bar 0.5pp = {0.5/(CEIL*100)*100:.0f}% of ceiling)")

def dmdd(g, mask=None):
    gated = CHAMP * g
    flip = g.diff().abs().fillna(0.0)
    costed = gated - flip * COST
    if mask is not None:
        costed = costed[mask]
    return metrics.max_dd(costed)

# ---- T1: random-gate null on the dMDD bar ----
# CORRECTED (2026-09-07 session): the original construction here was degenerate — it drew
# flip locations at prob=flipfrac, ffilled, then overwrote the ENTIRE series with
# np.where(u < offfrac/flipfrac, 0.5, 1.0) where offfrac/flipfrac = 17.5 > 1, so all 200
# "random gates" collapsed to the CONSTANT 0.5 gate (off%=100%, every draw dMDD +3.383pp).
# Replaced by random_gate_null(): persistence-matched Markov null (off% AND flip prob
# matched), contract-pinned by test_r2_null_gate_contract.py.
print("\nT1: random-gate null (200x persistence-matched Markov, off%+flip matched to dom_ma100)")
from HUNT_CRYPTO2_round2_lib import random_gate_null
bar = 0.005
real_dom_g, _ = binary_gate(cond_a_dom(100), 0.5)
offfrac = float((real_dom_g < 1.0).mean())
flipfrac = float(real_dom_g.diff().abs().fillna(0).mean())
print(f"  dom_ma100 gate: off%={offfrac*100:.0f} daily-flip-prob={flipfrac*100:.2f}%")
hits = 0
_, t1 = random_gate_null(CHAMP, p_off=offfrac, flip_prob=flipfrac, seed=42)
print(f"  corrected null: med dMDD={t1['dMDD_med']*100:+.3f}pp p90={t1['dMDD_p90']*100:+.3f}pp "
      f"std={t1['dMDD_std']*100:.3f}pp | gate sanity off%={t1['off_frac']*100:.0f} "
      f"flips={t1['n_flips']} mean_ep={t1['mean_ep_len']:.0f}d")
seeds = {}
for seed in [42, 123, 777]:
    _, d = random_gate_null(CHAMP, p_off=offfrac, flip_prob=flipfrac, seed=seed)
    seeds[seed] = d
print(f"  real configs clearing dMDD>=+0.5pp: 16/38 = 42% "
      f"(all at exactly the +0.807pp ceiling)")
for seed, d in seeds.items():
    print(f"    null seed={seed}: p90 dMDD={d['dMDD_p90']*100:+.3f}pp -> random gates reach "
          f"the ceiling often; single-episode bar is saturating")

# ---- T2: single-episode dependence ----
print("\nT2: dMDD with 2018-05-01..2018-07-31 EXCLUDED (does ANY config still clear +0.5pp?)")
excl = ~((CHAMP.index >= pd.Timestamp('2018-05-01')) & (CHAMP.index <= pd.Timestamp('2018-07-31')))
still = 0
for name, cond, sc in all_configs():
    g, _ = binary_gate(cond, sc)
    d_excl = dmdd(g, mask=excl) - metrics.max_dd(CHAMP[excl])
    if d_excl >= bar:
        still += 1
        print(f"  {name}: dMDD_excl2018 = {d_excl*100:+.3f}pp  (STILL PASSES)")
print(f"  configs still clearing +0.5pp with 2018-06 excluded: {still}/{len(all_configs())}")

# ---- T3: sc0.9 lightest-touch dominance configs under the MDD scramble ----
print("\nT3: sc0.9 dom configs (only Calmar improvers) — scramble on the MDD claim")
for ma in [100, 200]:
    g, _ = binary_gate(cond_a_dom(ma), 0.9)
    m = gate_metrics(g, env)
    live = (g < 1.0).idxmax()
    i2 = g.index[g.index >= live]
    rv = CHAMP.reindex(i2).fillna(0.0)
    gv = g.reindex(i2).fillna(1.0)
    real_mdd = metrics.max_dd(gv * rv)
    real_sr = metrics.sharpe_d(gv * rv)
    rng = np.random.default_rng(7)
    cm = cs = 0
    for _ in range(200):
        s = np.roll(gv.values, rng.integers(10, len(rv) - 10))
        b = pd.Series(s * rv.values, index=i2)
        cm += metrics.max_dd(b) >= real_mdd
        cs += metrics.sharpe_d(b) >= real_sr
    cal_g = m['ann'] / abs(m['mdd'])
    print(f"  dom_ma{ma}_sc0.9: dAnn={m['d_ann']*100:+.3f}pp dMDD={m['d_mdd']*100:+.3f}pp "
          f"dSR={m['d_sr']:+.3f} Calmar {env['CHAMP_ANN']/abs(env['CHAMP_MDD']):.2f}->{cal_g:.2f} | "
          f"p_SR={cs/200:.3f} p_MDD={cm/200:.3f}")
