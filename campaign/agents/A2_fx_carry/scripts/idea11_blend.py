"""Idea 11: FX multi-signal blend = carry(+accrual) + tsmom252 + ratemom6m, equal-weight of net series."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

px = F.spots("2006-01-01")
y = F.yields8(); ym = y.resample("MS").mean()
diff = ym.sub(ym["USD"], axis=0).drop(columns=["USD"])

comps = {}

# A) carry + accrual (7pair, 2018+)
pxA = px.dropna(how="all").loc["2018-01-01":]
sig = diff.reindex(pxA.index).ffill()
ranks = sig.rank(axis=1, ascending=False); n_ok = sig.notna().sum(axis=1)
pos = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
for c in sig.columns:
    pos[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
posA = monthly(pos.where(sig.notna(), 0.0)).loc["2018-07-02":]
accr = diff.reindex(pxA.index).ffill()/100/252
frA = pxA.pct_change().shift(-1) + accr.shift(-1)
comps["carry"] = F.net_of((posA*frA).sum(axis=1, min_count=1), posA)

# B) tsmom 252d, 4pair, 2006+
cols = ["EUR","GBP","JPY","CAD"]
m = np.sign(px[cols].pct_change(252))
w = m.div(m.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
posB = monthly(w).loc["2006-07-01":]
comps["tsmom252"] = F.net_of(F.t1_pnl(posB, px[cols]), posB)

# C) ratemom 6m top2/bottom2 7pair
s = diff.diff(6).reindex(px.index).ffill()
ranks = s.rank(axis=1, ascending=False); n_ok = s.notna().sum(axis=1)
p = pd.DataFrame(0.0, index=s.index, columns=s.columns)
for c in s.columns:
    p[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
posC = monthly(p.where(s.notna(), 0.0)).loc["2018-07-02":]
comps["ratemom6m"] = F.net_of(F.t1_pnl(posC, px), posC)

df = pd.DataFrame(comps).dropna(how="all").fillna(0.0)
print("corr:\n", df.corr().round(2))
for wt in (df.columns, ["carry","tsmom252"]):
    r = df[list(wt)].mean(axis=1)
    r = F.util.vol_target(r).dropna()
    F.report("blend_"+"_".join(wt), r)
    sr, p = F.scramble(r, r)
