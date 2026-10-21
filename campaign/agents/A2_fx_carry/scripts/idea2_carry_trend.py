"""Idea 2: carry gated by 50d trend. Hold carry position only where 50d trend of the pair agrees."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

px = F.spots("2006-01-01")
y = F.yields8()
diff = y.sub(y["USD"], axis=0).drop(columns=["USD"]).ffill()
sig = diff.reindex(px.index).ffill()

def ranks_to_pos(sig, w=0.25):
    ranks = sig.rank(axis=1, ascending=False); n_ok = sig.notna().sum(axis=1)
    pos = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    for c in sig.columns:
        pos[c] = np.where(ranks[c] <= 2, w, np.where(ranks[c] > n_ok-2, -w, 0.0))
    return pos.where(sig.notna(), 0.0)

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

for tag, cols, start in [("7pair", None, "2018-07-02"), ("4pair_fred", ["EUR","GBP","JPY","CAD"], "2006-01-03")]:
    cc = list(sig.columns) if cols is None else cols
    s = sig[cc]; p0 = monthly(ranks_to_pos(s))
    tr = px[cc].rolling(50).mean()
    trend = np.sign(px[cc] - tr)                     # +1 uptrend of foreign vs USD
    p = p0 * (trend > 0)                             # keep only long-carry legs in uptrend
    # symmetric: for shorts (pos<0) require downtrend
    p = p0 * np.where(p0 > 0, (trend > 0).astype(float), np.where(p0 < 0, (trend < 0).astype(float), 0.0))
    p = p.loc[start:]
    pnl = F.t1_pnl(p, px[cc]); r = F.net_of(pnl, p)
    F.report(f"carry_trend_{tag}", r)
    # daily version too (rebalance daily signal, same gate)
    p1 = (p0 * np.where(p0 > 0, (trend>0).astype(float), np.where(p0<0,(trend<0).astype(float),0.0))).loc[start:]
    r1 = F.net_of(F.t1_pnl(p1, px[cc]), p1)
    F.report(f"carry_trend_daily_{tag}", r1)
