"""Idea 1: FX carry — rank currencies by (foreign 10y - US 10y) diff, monthly.
Long top-2 (+0.25 ea), short bottom-2 (-0.25 ea) vs USD -> gross 1.0. T+1, 6bps/side, 10% vol target."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

px = F.spots("2006-01-01")
y = F.yields8()
diff = y.sub(y["USD"], axis=0)          # foreign minus US, monthly
diff = diff.drop(columns=["USD"]).ffill()
sig = diff.reindex(px.index).ffill()    # daily forward-filled signal

def carry_book(sig, px, long_n=2, short_n=2, w=0.25, start="2018-07-02"):
    ranks = sig.rank(axis=1, ascending=False)      # 1 = highest yield
    n_ok = sig.notna().sum(axis=1)
    pos = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for c in sig.columns:
        pos[c] = np.where(ranks[c] <= long_n, w, np.where(ranks[c] > n_ok - short_n, -w, 0.0))
    pos = pos.where(sig.notna(), 0.0)
    # monthly-only trading: hold signal as of month start
    mstart = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    pos_m = pos.loc[mstart].reindex(pos.index).ffill().fillna(0.0)
    return pos_m.loc[start:]

for start, tag in [("2018-07-02","7pair"), ("2006-01-03","4pair_fred")]:
    cols = sig.columns if tag=="7pair" else ["EUR","GBP","JPY","CAD"]
    p = carry_book(sig[cols], px[cols], start=start)
    pnl = F.t1_pnl(p, px[cols])
    r = F.net_of(pnl, p)
    F.report(f"carry_{tag}", r)
