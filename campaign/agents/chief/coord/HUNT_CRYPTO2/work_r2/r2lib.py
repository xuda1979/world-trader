"""Shared round-2 helpers (importable, testable form of the HUNT_CRYPTO2_round2.py gates)."""
import numpy as np, pandas as pd
from bt import metrics


def scramble_counts(g, ref, n=200, seed=7):
    """Block-roll the gate series `g` vs book `ref` n times.

    Returns (p_mdd, real_mdd) where
      p_mdd = P(max_dd(scrambled) >= real_mdd)  -- random placement at least as SHALLOW.
    Drawdowns are negative (metrics.max_dd), so '>= real' = 'at least as shallow as real'.
    A gate with genuine DD-avoidance skill has no random placement matching it -> p_mdd small.
    """
    r = ref.values
    gv = g.values
    real = metrics.max_dd(pd.Series(gv * r, index=ref.index))
    rng = np.random.default_rng(seed)
    T = len(r)
    cnt = 0
    for _ in range(n):
        s = np.roll(gv, rng.integers(10, T - 10))
        if metrics.max_dd(pd.Series(s * r, index=ref.index)) >= real:
            cnt += 1
    return cnt / n, real
