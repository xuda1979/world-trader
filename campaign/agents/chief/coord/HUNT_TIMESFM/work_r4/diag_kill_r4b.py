"""Corrected diagnostics: proper sign-vs-sign hit rate, excl-Mar2020 delta, yearly deltas."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
import eval_sleeves as E
import eval_b_overlay as B
from bt import metrics

print("=== (a) corrected dir-hit (sign fcst vs sign next-day ret) ===")
for a in E.ASSETS:
    f = pd.read_csv(f"{E.OUT}/fcst_{a}.csv", parse_dates=["date"]).set_index("date")
    m = (f["f"] - f["last"]).values
    px = E.close(a)
    r = px.pct_change().reindex(f.index)
    nxt = np.sign(r.shift(-1).fillna(0.0).values)
    hit = float((np.sign(m) == nxt).mean())
    up = float((m > 0).mean())
    print(f"  {a}: dir-hit={hit:.4f} (up-fcst share={up:.3f})")

print("=== (b) excl-Mar2020 + yearly delta anatomy ===")
cand = B.pct_rank_mask(B.mag_pool)
b1 = B.pct_rank_mask(B.rvp)
_, net_c, _ = B.ovl_delta(cand)
_, net_1, _ = B.ovl_delta(b1)
idx = net_c.index
CHm = B.CH.reindex(idx)
excl = (idx < "2020-03-01") | (idx > "2020-04-30")
d_c_full = (net_c - CHm).dropna()
d_c = (net_c - CHm)[excl].dropna(); d_1 = (net_1 - CHm)[excl].dropna()
print(f"  full:  cand dSR={metrics.sharpe_d(d_c_full):+.3f}")
print(f"  excl Mar-Apr20: cand dSR={metrics.sharpe_d(d_c):+.3f}  b1 dSR={metrics.sharpe_d(d_1):+.3f}")
yr = d_c_full.groupby(d_c_full.index.year).apply(lambda x: x.sum())
print("  yearly dSR-arithmetic-sum (bp):", {int(k): round(v*1e4) for k, v in yr.items() if abs(v) > 1e-5})
top8 = d_c_full.abs().sort_values(ascending=False).head(8)
print(f"  top-8 |delta| days sum={d_c_full.loc[top8.index].sum()*1e4:.0f}bp "
      f"vs full-window total={d_c_full.sum()*1e4:.0f}bp")
