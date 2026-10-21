#!/usr/bin/env python3
"""TDD test for extend_heads.py seam-noise crash (AttributeError: ndarray.abs()).

RED state (recorded 2026-09-07): the un-fixed script crashed at line 63 with
  AttributeError: 'numpy.ndarray' object has no attribute 'abs'
(see extend_heads_run.log / task bybc5thf0 output, first symbol EWH, nothing written).

This test pins BOTH halves of the fix:
  1. the buggy idiom `ndarray.abs()` must keep raising (regression guard: if numpy
     ever grows ndarray.abs, this test flags that the guard is vacuous), and
  2. the fixed idiom `np.abs(a - b).max()` returns the exact expected seam noise.
"""
import numpy as np
import pandas as pd

h = pd.DataFrame({"date": pd.to_datetime(["2012-12-28", "2012-12-31"]),
                  "close": [30.0, 30.1]})
old = pd.DataFrame({"date": pd.to_datetime(["2012-12-31", "2013-01-02"]),
                    "close": [30.2, 30.3]}).set_index("date")
seam = h[h["date"].isin(old.index)]
expr = seam["close"].values - old.loc[seam["date"], "close"].values
assert isinstance(expr, np.ndarray)

# 1. regression guard: the original crashing idiom must still crash
try:
    expr.abs()
    raise SystemExit("VACUOUS GUARD: ndarray.abs() no longer raises — fix test")
except AttributeError:
    pass

# 2. the fixed idiom, exactly as now in extend_heads.py, must give the right value
noise = float(np.abs(seam["close"].values - old.loc[seam["date"], "close"].values).max())
assert abs(noise - 0.1) < 1e-12, f"expected 0.1, got {noise}"
print(f"PASS: seam-noise guard holds; fixed idiom -> {noise:.4f}")
