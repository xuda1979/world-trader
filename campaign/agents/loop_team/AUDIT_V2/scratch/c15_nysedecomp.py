#!/usr/bin/env python3
"""Hypothesis: V2 moved the federal-smeared chunk to the holiday row.
Check: v2_hol - v2_next ≈ 0.5*(fix_hol + fix_next) i.e. the smeared chunk re-split?
Direct test: sum over (hol, next) pairs: fix sum vs v2 sum. And regress per-pair."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import HOL, NEW, load
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fix = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fixs = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fixa = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dies = load(NEW['diescrack']); cfx = load(NEW['CFX4'])
rows = []
for d in sorted(d for d in v2.index if d.date() in HOL):
    nxt = d + pd.Timedelta(days=1)
    if nxt not in v2.index: continue
    fh = fix[d] if d in fix.index else np.nan
    fn = fix[nxt] if nxt in fix.index else np.nan
    rows.append(dict(date=d, hol=v2[d], nxt=v2[nxt], sum_v2=v2[d]+v2[nxt],
                     fixhol=fh, fixnxt=fn, sum_fix=fh+fn,
                     hol_s=v2s[d], nxt_s=v2s[nxt], hol_a=v2a[d], nxt_a=v2a[nxt],
                     dies_hol=float(dies[d]) if d in dies.index else 0.0,
                     cfx_hol=float(cfx[d]) if d in cfx.index else 0.0,
                     dies_nxt=float(dies[nxt]) if nxt in dies.index else 0.0,
                     cfx_nxt=float(cfx[nxt]) if nxt in cfx.index else 0.0))
df = pd.DataFrame(rows)
print(f"pairs: {len(df)}; sum(v2 hol+nxt) vs sum(fix hol+nxt): mean|diff| {(df.sum_v2-df.sum_fix).abs().mean():.6f}")
print(df[['date','hol','nxt','fixhol','fixnxt','sum_v2','sum_fix']].head(8).to_string())
# is v2_hol just the COST row (approx constant)? correlate with what?
print(f"\nv2_hol stats: mean {df.hol.mean():.6f} std {df.hol.std():.6f} min {df.hol.min():.6f} max {df.hol.max():.6f}")
print(f"SAFE==AGGR on hol rows: {(df.hol_s-df.hol_a).abs().max():.2e}; on nxt rows: {(df.nxt_s-df.nxt_a).abs().max():.2e}")
# regression of hol row on candidate terms: -cost (const-ish) + small w*new?
X = np.column_stack([np.ones(len(df)), df.dies_hol, df.cfx_hol, df.hol_s, df.hol_a])
coef, _, _, _ = np.linalg.lstsq(X, df.hol.values, rcond=None)
print(f"hol ~ 1 + dies + cfx + safe + aggr: c={coef[0]:.6f} wd={coef[1]:.4f} wc={coef[2]:.4f} ws={coef[3]:.4f} wa={coef[4]:.4f}")
print(f"resid max {np.abs(df.hol.values - X@coef).max():.3e}")
