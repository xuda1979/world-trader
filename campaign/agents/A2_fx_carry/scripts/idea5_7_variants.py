"""Ideas 5-7: rate-diff momentum, DXY trend mapped to pairs, VIX-gated safe havens."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A2_fx_carry/scripts")
import numpy as np, pandas as pd
import fx_lib as F

def monthly(pos):
    m = pos.groupby([pos.index.year, pos.index.month]).head(1).index
    return pos.loc[m].reindex(pos.index).ffill().fillna(0.0)

px = F.spots("2006-01-01")
y = F.yields8()
diff = y.sub(y["USD"], axis=0).drop(columns=["USD"])
diff_d = diff.reindex(px.index).ffill()

# ---- Idea 5: rate-diff momentum (3m change), top2/bottom2 monthly
for k in (1, 3):  # 1 or 3 month change in yield diff
    mom = diff.diff(k).ffill()
    s = mom.reindex(px.index).ffill()
    ranks = s.rank(axis=1, ascending=False); n_ok = s.notna().sum(axis=1)
    p = pd.DataFrame(0.0, index=s.index, columns=s.columns)
    for c in s.columns:
        p[c] = np.where(ranks[c] <= 2, 0.25, np.where(ranks[c] > n_ok-2, -0.25, 0.0))
    p = monthly(p.where(s.notna(), 0.0))
    for cols, tag, start in [(list(s.columns), "7pair", "2018-07-02"),
                             (["EUR","GBP","JPY","CAD"], "4pair", "2018-07-02")]:
        pp = p[cols].loc[start:]
        r = F.net_of(F.t1_pnl(pp, px[cols]), pp)
        F.report(f"ratemom{k}m_{tag}", r)

# ---- Idea 6: DXY 252d trend -> fade foreign ccys (long USD trend)
dxy = F._fred("dxy")
for L in (126, 252):
    sgn = np.sign(dxy.pct_change(L)).reindex(px.index).ffill()
    cols = ["EUR","GBP","JPY","CAD"]
    p = pd.DataFrame(np.tile(-sgn.values[:,None]/4.0, (1, len(cols))),
                     index=px.index, columns=cols)
    p = (p.where(sgn.notna(), 0.0) if sgn is not None else p)
    pp = monthly(p.fillna(0.0)).loc["2006-07-01":]
    r = F.net_of(F.t1_pnl(pp, px[cols]), pp)
    F.report(f"dxy_tsmom{L}", r)

# ---- Idea 7: VIX-gated long JPY (+CHF 2019+), vol-scaled
vix = F._fred("vix")
vix_hi = (vix > vix.rolling(252).quantile(0.8)).astype(float).reindex(px.index).ffill().fillna(0.0)
for cols, tag, start in [(["JPY"], "jpy", "2006-07-01"), (["JPY","CHF"], "jpy_chf", "2019-07-01")]:
    p = pd.DataFrame(0.0, index=px.index, columns=cols)
    for c in cols:
        vol = px[c].pct_change().rolling(21).std()*np.sqrt(252)
        p[c] = (vix_hi / vol.clip(0.05)).div(1.0).fillna(0.0)
    p = p.div(p.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)  # gross<=1
    pp = p.loc[start:]
    r = F.net_of(F.t1_pnl(pp, px[cols]), pp)
    F.report(f"vixgate_{tag}", r)
