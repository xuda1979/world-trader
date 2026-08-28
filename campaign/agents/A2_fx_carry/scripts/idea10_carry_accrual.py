"""Idea 10: TRUE carry = spot return + daily accrual of (foreign10y - us10y)/252.
Top2/bottom2 by yield diff, monthly, gross 1. 7pair from 2018-07 (when foreign yields start)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

px = F.spots("2018-01-01")
y = F.yields8()
ym = y.resample("MS").mean()
diff = ym.sub(ym["USD"], axis=0).drop(columns=["USD"])          # monthly yield diff
diff_d = diff.reindex(px.index).ffill()                          # daily accrual rate
accr = diff_d / 100.0 / 252.0

sig = diff.reindex(px.index).ffill()
ranks = sig.rank(axis=1, ascending=False); n_ok = sig.notna().sum(axis=1)
pos = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
for c in sig.columns:
    pos[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
pos = monthly(pos.where(sig.notna(), 0.0)).loc["2018-07-02":]

fr_spot = px.pct_change().shift(-1)
fr = fr_spot + accr.shift(-1)                                    # carry-adjusted fwd return
pnl = (pos * fr).sum(axis=1, min_count=1)
r = F.net_of(pnl, pos)
F.report("carry_accrual_7pair", r)

# variant: pure accrual harvest (no spot), i.e. classic forward-premium book
pnl2 = (pos * accr.shift(-1)).sum(axis=1, min_count=1)
r2 = F.net_of(pnl2, pos)
F.report("carry_accrualonly_7pair", r2)
