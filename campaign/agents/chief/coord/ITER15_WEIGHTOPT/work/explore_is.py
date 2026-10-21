#!/usr/bin/env python3
"""ITER15 WEIGHTOPT — step 1: characterize the IS window sleeve matrix.

Loads the EXACT 13 sleeve paths from the canonical builder (rawew13v2_build.py),
restricted to the IS window (< 2017-01-01), and reports per-sleeve IS SR, the IS
correlation matrix, and the current heuristic relw. Read-only; no champion writes.
"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd

import importlib.util
spec = importlib.util.spec_from_file_location(
    "rb", "/Users/daxu/software/world-trader/campaign/scripts/rawew13v2_build.py")
rb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rb)

ROOT = "/Users/daxu/software/world-trader"
NAMES = rb.NAMES
PATHS = rb.PATHS
IS_END = rb.IS_END

df = pd.DataFrame({n: rb.load(PATHS[n]).dropna() for n in NAMES})
df = df[df.index >= '2008-03-31']
print(f"full span: {df.index.min().date()} .. {df.index.max().date()}  rows={len(df)}")

isr = df[df.index < IS_END]
print(f"IS  span: {isr.index.min().date()} .. {isr.index.max().date()}  rows={len(isr)}")
oos = df[df.index >= IS_END]
print(f"OOS span: {oos.index.min().date()} .. {oos.index.max().date()}  rows={len(oos)}")
print()

# per-sleeve coverage inside IS
print("per-sleeve IS coverage (non-null days in IS window):")
for n in NAMES:
    nn = isr[n].notna().sum()
    print(f"  {n:10s} n={nn:5d}  first={isr[n].first_valid_index()}")

print()
SR = pd.Series({n: rb.is_sr(isr[n]) for n in NAMES})
relw = np.maximum(SR, 0.0) ** rb.P
out = pd.DataFrame({"IS_SR": SR, "relw": relw})
out["share"] = out.relw / out.relw.sum()
print("IS SR and heuristic relw (P=0.55):")
print(out.sort_values("relw", ascending=False).to_string(float_format=lambda x: f"{x:.4f}"))
print()

# correlation on the common IS block. CFX4 has ZERO IS coverage (relw=0), so it is
# excluded here; the other 12 share a common block.
IS_HAVE = [n for n in NAMES if isr[n].notna().sum() > 0]
com = isr[IS_HAVE].dropna()
print(f"common-block IS rows ({len(IS_HAVE)} pre-2017 sleeves, CFX4 excluded): {len(com)}")
cm = com.corr()
print("\nIS correlation matrix:")
print(cm.to_string(float_format=lambda x: f"{x:+.2f}"))
print()

# brwt family concentration
brwt = ["brwt5", "brwt7", "brwt10", "brwt15"]
print("brwt family pairwise corr:")
print(com[brwt].corr().to_string(float_format=lambda x: f"{x:+.3f}"))
print(f"\nbrwt family combined relw share: {out.loc[brwt,'share'].sum():.4f}")
print(f"effective independent bets (1/sum(w_i^2) on relw shares): "
      f"{1/ (out.share**2).sum():.2f}")
