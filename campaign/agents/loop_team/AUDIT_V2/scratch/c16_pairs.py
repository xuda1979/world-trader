#!/usr/bin/env python3
"""Compare my no-smear L13 rebuild vs V2 on (holiday, next) pairs; test whether V2 hol rows
are cost-only and where the 11-pool hol gross went."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from c8_l13 import build13v2
from v2lib import HOL
ROOT = "/Users/daxu/software/world-trader"
v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
A, stA = build13v2(0.07, 0.04)
Bp, stB = build13v2(0.091, 0.03)
BAL = ((A+Bp)/2).dropna()
pairs = []
for d in sorted(dd for dd in v2.index if dd.date() in HOL):
    nxt = d + pd.Timedelta(days=1)
    if nxt not in v2.index: continue
    pairs.append((d, float(v2[d]), float(BAL[d]) if d in BAL.index else np.nan,
                  float(v2[nxt]), float(BAL[nxt]) if nxt in BAL.index else np.nan))
df = pd.DataFrame(pairs, columns=['date','v2_hol','my_hol','v2_nxt','my_nxt']).set_index('date')
df['v2_pair'] = df.v2_hol + df.v2_nxt
df['my_pair'] = df.my_hol + df.my_nxt
df['pair_diff'] = df.v2_pair - df.my_pair
df['hol_diff'] = df.v2_hol - df.my_hol
print(df.head(10).to_string())
print(f"\npair sums: mean|diff| {df.pair_diff.abs().mean():.6f}; hol rows: mean|diff| {df.hol_diff.abs().mean():.6f}")
# correlation of hol_diff with |gs change| day-over-day (cost explanation)
gs = stA['gs']; gsd = gs.diff().abs()
hd = df.hol_diff.dropna()
g = gsd.reindex(hd.index)
print(f"corr(hol_diff, |d gs|) = {hd.corr(g):.3f}")
print(f"corr(v2_hol, |d gs|) = {df.v2_hol.corr(gsd.reindex(df.index)):.3f}")
print(f"mean |d gs| on hol rows: {g.mean():.4f}; est reb cost 6e-4*|dgs| mean = {6e-4*g.mean():.6f}")
