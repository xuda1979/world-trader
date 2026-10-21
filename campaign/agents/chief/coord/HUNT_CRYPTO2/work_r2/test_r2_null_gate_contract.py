#!/usr/bin/env python3
"""TDD: persistence-matched random-gate null for the R2 dMDD bar (AUDIT T1 was broken).

The old T1 drew flip-locations with prob=flipfrac (1.21%), ffilled them, then overwrote
the WHOLE series with `np.where(u < offfrac/flipfrac, 0.5, 1.0)` where offfrac/flipfrac
= 17.5 > 1  ->  every draw returned the CONSTANT 0.5 gate (off%=100%, all 200 dMDD
identical). A constant gate is not a 'random gate placement' null: it has no episodes,
no timing variance, and its +3.38pp dMDD is just the flat-de-risk dial.

Contract under test (random_gate_null):
  1. off-fraction matches target (±2pp)
  2. gates have REAL episodes: >= 20 flips per draw, mean episode length within 3x of
     1/p10 implied by the matched flip prob (i.e. NOT constant, NOT all-off)
  3. draws are heterogeneous: stdev of per-draw dMDD > 0
"""
import sys
import numpy as np, pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")

from HUNT_CRYPTO2_round2_lib import load_env, random_gate_null

env = load_env()
CHAMP = env['CHAMP']
T = len(CHAMP)

g, diag = random_gate_null(CHAMP, p_off=0.212, flip_prob=0.0121, seed=42)

# 1. off-fraction matched
assert abs(diag['off_frac'] - 0.212) <= 0.02, f"off% {diag['off_frac']:.3f} != 0.212"
# 2. real episodes (the old construction: flips=0 or 1 -> fails here)
assert diag['n_flips'] >= 20, f"gate is ~constant: only {diag['n_flips']} flips"
assert diag['mean_ep_len'] < 3 * 1 / 0.0121, f"episodes too long: {diag['mean_ep_len']:.0f}d"
# 3. heterogeneity across draws
assert diag['dMDD_std'] > 1e-6, f"all draws identical (std={diag['dMDD_std']:.2e})"
# values restricted to the gate alphabet
assert set(np.unique(g.values)) <= {1.0, 0.5}, f"unexpected gate values {set(np.unique(g.values))}"
print(f"PASS: null gates off%={diag['off_frac']*100:.1f} flips={diag['n_flips']} "
      f"mean_ep={diag['mean_ep_len']:.0f}d dMDD spread std={diag['dMDD_std']*100:.3f}pp")
