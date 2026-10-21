#!/usr/bin/env python3
"""TDD: scramble_gate DD-claim p-value DIRECTION (round-2 verdict bug).

Convention under test (matches metrics.max_dd: drawdowns are NEGATIVE):
  p_MDD must = P(random gate at least as SHALLOW as real) = P(max_dd(scrambled) >= real).
  A gate de-risking exactly the champ's DD window has genuine DD-avoidance skill ->
  random placement rarely matches it -> p_MDD <= 0.05.
  A gate de-risking somewhere irrelevant is reproduced by random placement -> p_MDD large.
The OLD implementation counted P(max_dd(scrambled) <= real) (deeper-than), i.e. 1-p, which
INVERTS the pass/fail on the charter's MDD leg.
"""
import sys
import numpy as np, pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_CRYPTO2/work_r2")
from r2lib import scramble_counts  # corrected implementation under test

ANN = 252
rng = np.random.default_rng(11)
T = 1500
base = rng.normal(0.0004, 0.006, T)                       # calm book
crash = slice(700, 760)                                   # one 60d crash window
base[crash] -= 0.02                                       # deep single DD episode
champ = pd.Series(base, index=pd.bdate_range("2020-01-01", periods=T))

off = np.ones(T)
off[crash] = 0.5                                          # SKILL: off exactly during the crash
skilled = pd.Series(off, index=champ.index)

off2 = np.ones(T)
off2[: int(0.25 * T)] = 0.5                               # NO SKILL: off during a calm stretch
unskilled = pd.Series(off2, index=champ.index)

always = pd.Series(np.ones(T), index=champ.index)


def sd(s):
    return float((s.values * champ.values).__abs__().sum() * 0)  # placeholder, unused


def real_dd(g):
    from bt import metrics
    return metrics.max_dd(pd.Series(g.values * champ.values, index=champ.index))


p_skill, dd_skill = scramble_counts(skilled, champ)
p_unsk, dd_unsk = scramble_counts(unskilled, champ)
p_alw, dd_alw = scramble_counts(always, champ)

print(f"skilled  gate: real MDD={dd_skill*100:.2f}%  p_MDD={p_skill:.3f}")
print(f"unskilled gate: real MDD={dd_unsk*100:.2f}%  p_MDD={p_unsk:.3f}")
print(f"always-on     : real MDD={dd_alw*100:.2f}%  p_MDD={p_alw:.3f}")

assert dd_skill > dd_alw - 1e-12, "skilled gate must be shallower than always-on"
assert p_skill <= 0.05, f"skilled gate must have p_MDD<=0.05, got {p_skill:.3f}"
assert p_alw >= 0.5, f"always-on gate (no skill, no variance) must NOT pass, got {p_alw:.3f}"
assert p_unsk > 0.05, f"irrelevant de-risk must be reproduced by random placement, got {p_unsk:.3f}"
print("PASS: p_MDD direction correct (skill -> small p; random/none -> large p)")
