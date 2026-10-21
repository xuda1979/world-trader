#!/usr/bin/env python3
"""AUDIT_GATES2 R3 (b) — NOT-A-GATE guard (regression lock, runs in <1s).

The composition-preserving scramble (r3b_composition_scramble.py) is a DIAGNOSTIC.
Charter: never wire it into bt.gates.run. This lock fails if:
  (1) any bt/ module references the r3b diagnostic functions or np.roll on a whole
      weight matrix inside gates.run;
  (2) gates.run's result dict sprouts a composition-scramble key.
Usage: python3 campaign/agents/chief/coord/AUDIT_GATES2/r3/not_a_gate_guard.py  (exit 0 = clean)
"""
import sys, inspect

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt import gates as G  # noqa: E402

failures = []
src = inspect.getsource(G.run)
names = set(G.run.__code__.co_names)
forbidden = ("composition", "common_lag", "per_slot", "champion_weights")
for f in forbidden:
    if f in src:
        failures.append(f"gates.run source mentions '{f}'")
    if f in names:
        failures.append(f"gates.run references '{f}'")
if "np.roll" in src:
    failures.append("gates.run calls np.roll (signal-scramble must live in scramble_positions)")
expected_keys = {"sr", "scr_p", "scr_ok", "pass"}
import numpy as np, pandas as pd
idx = pd.bdate_range("2020-01-01", periods=400)
r = pd.Series(np.random.default_rng(1).normal(3e-4, 0.01, 400), index=idx)
res = G.run(r, ref=None, sig=None)
extra = {k for k in res if "comp" in k.lower() or "lag" in k.lower()}
if extra:
    failures.append(f"gates.run result has composition-like keys: {extra}")
if failures:
    print("NOT-A-GATE GUARD: FAIL")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("NOT-A-GATE GUARD: OK (composition-preserving scramble stays out of bt.gates.run)")
