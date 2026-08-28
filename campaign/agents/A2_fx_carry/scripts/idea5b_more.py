"""Idea 5 (fixed): monthly rate-diff momentum. Idea 8: 1260d FX reversal (value proxy).
Idea 9: single-pair JPY/CHF trend sweep."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

px = F.spots("2000-01-01")
y = F.yields8()
ym = y.resample("MS").mean()                      # one row per month
diff = ym.sub(ym["USD"], axis=0).drop(columns=["USD"])

# ---- Idea 5 fixed: k-month change in yield diff, top2/bottom2, monthly book
for k in (3, 6):
    mom = diff.diff(k)
    s = mom.reindex(px.index).ffill()
    ranks = s.rank(axis=1, ascending=False); n_ok = s.notna().sum(axis=1)
    p = pd.DataFrame(0.0, index=s.index, columns=s.columns)
    for c in s.columns:
        p[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
    p = monthly(p.where(s.notna(), 0.0)).loc["2018-07-01":]
    r = F.net_of(F.t1_pnl(p, px), p)
    F.report(f"ratemom{k}m_7pair", r)

# ---- Idea 8: long-horizon reversal: buy 3y losers vs USD, vol-scaled, monthly (4 pairs 2000+)
for L in (756, 1260):
    cols = ["EUR","GBP","JPY","CAD"]
    rev = -np.sign(px[cols].pct_change(L))
    w = rev.div(px[cols].pct_change().rolling(21).std().mul(np.sqrt(252)).clip(0.05), axis=0)
    w = w.div(w.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    p = monthly(w).loc["2006-01-01":]
    r = F.net_of(F.t1_pnl(p, px[cols]), p)
    F.report(f"reversal{L}_4pair", r)

# ---- Idea 9: single-pair JPY and CHF trend, sweep lookbacks, daily+monthly
for c in ("JPY","CHF"):
    for L in (63, 126, 252):
        s = px[[c]].dropna().loc["2006-01-01":]
        pos = np.sign(s.pct_change(L)).div(
            s.pct_change().rolling(21).std().mul(np.sqrt(252)).clip(0.05), axis=0).fillna(0.0)
        r = F.net_of(F.t1_pnl(pos, s), pos)
        F.report(f"ts{c}_{L}_day", r)
