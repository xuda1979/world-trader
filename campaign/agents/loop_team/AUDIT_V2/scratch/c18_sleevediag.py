#!/usr/bin/env python3
"""Localize small sleeve rebuild diffs; then recompute sleeve gate claims (check 2)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import importlib
import c17_sleeves as S
ROOT = "/Users/daxu/software/world-trader"

# ---- localize diescrack diff ----
out, pos, net = S.rebuild_diescrack()
ref = pd.read_csv(S.DIE, index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([ref.rename('ref'), out.rename('mine')], axis=1).dropna()
d = (j.ref - j.mine).abs()
print(f"diescrack: rows|diff|>1e-9: {(d>1e-9).sum()}, >1e-12: {(d>1e-12).sum()}")
print(d.sort_values(ascending=False).head(5))
# ---- localize CFX4 diff ----
out2 = S.rebuild_cfx4()
refc = pd.read_csv(S.CFX, index_col=0, parse_dates=True).iloc[:,0]
jc = pd.concat([refc.rename('ref'), out2.rename('mine')], axis=1).dropna()
dc = (jc.ref - jc.mine).abs()
print(f"\nCFX4: rows|diff|>1e-9: {(dc>1e-9).sum()}, >1e-12: {(dc>1e-12).sum()}, >1e-6: {(dc>1e-6).sum()}")
print(dc.sort_values(ascending=False).head(8))
