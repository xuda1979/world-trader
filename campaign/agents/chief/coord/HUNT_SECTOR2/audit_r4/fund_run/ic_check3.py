"""Annual IC by VINTAGE with stale-data carry-forward: FY y score stays active until
FY y+1 becomes available (Jul-1 y+2... no: Jul-1 of y+1). A name with no new FY keeps
its last score until its price series dies. Window: [avail_y, next_avail) per name."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import load_panel, FUND
import numpy as np, pandas as pd

px, rets = load_panel()
F = pd.read_parquet(FUND)
F = F[F.symbol.isin(px.columns)].copy()

def zsc(f2, x):
    med = x.groupby(f2["fy"]).transform("median")
    sd = x.groupby(f2["fy"]).transform(lambda s: s.std())
    return ((x - med) / sd.where(sd > 0)).clip(-3, 3)

def score_value(f):
    eb = f.net_income / f.equity.replace(0, np.nan)
    ic = (f.equity + f.debt - f.cash).where(lambda s: s > 0)
    oic = f.op_income / ic
    sta = f.revenue / f.total_assets.where(lambda s: s > 0)
    legs = pd.DataFrame({"eb": eb, "oic": oic, "sta": sta})
    out = pd.Series(np.nan, index=f.index)
    for c in legs.columns:
        out = out.add(zsc(f, legs[c]), fill_value=0)
    n = legs.notna().sum(axis=1)
    return (out / n.where(n > 0)).where(n > 0)

def score_prof(f):
    oi = f.op_income / f.total_assets.where(lambda s: s > 0)
    ni = f.net_income / f.total_assets.where(lambda s: s > 0)
    legs = pd.DataFrame({"oi": oi, "ni": ni})
    out = pd.Series(np.nan, index=f.index)
    for c in legs.columns:
        out = out.add(zsc(f, legs[c]), fill_value=0)
    n = legs.notna().sum(axis=1)
    return (out / n.where(n > 0)).where(n > 0)

def _dy(f2, col, g):
    return (f2[col] - g[col].shift(1)) / f2.total_assets.where(lambda s: s > 0)

def score_growth(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    legs = pd.DataFrame({"d_rev": _dy(f2, "revenue", g), "d_oi": _dy(f2, "op_income", g)})
    out = pd.Series(np.nan, index=f2.index)
    for c in legs.columns:
        out = out.add(zsc(f2, legs[c]), fill_value=0)
    n = legs.notna().sum(axis=1)
    return (out / n.where(n > 0)).where(n > 0)

def score_accrual_inv(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    acc = ((f2.receivables - g.receivables.shift(1)) + (f2.inventory - g.inventory.shift(1))
           - (f2.payables - g.payables.shift(1))) / f2.total_assets.where(lambda s: s > 0)
    return -zsc(f2, acc)

def score_piotroski(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    ta = f2.total_assets.where(lambda s: s > 0)
    roa = f2.net_income / ta
    droa = roa - pd.Series(g.net_income.apply(lambda x: (x / x.total_assets.where(lambda s: s > 0))).apply(lambda s: s.shift(1)).values if False else
                           (f2.net_income / ta).groupby(f2.symbol).shift(1).values, index=f2.index)
    leg1 = (roa > 0).astype(float).where(f2.net_income.notna())
    leg2 = (roa > roa.groupby(f2.symbol).shift(1)).astype(float).where(f2.net_income.notna())
    shg = f2.shares.groupby(f2.symbol).pct_change()
    leg3 = (shg <= 0).astype(float).where(f2.shares.notna())
    return leg1.fillna(0) + leg2.fillna(0) + leg3.fillna(0)

def score_momentum_qual(f):
    # value x prof interaction: only among names with both
    v = score_value(f); p = score_prof(f)
    return (v + p) / 2

SCORES = {"value": score_value, "prof": score_prof, "growth": score_growth,
          "accrual_inv": score_accrual_inv, "piotroski3": score_piotroski,
          "v+p": score_momentum_qual}

for name, fn in SCORES.items():
    f = F.copy().sort_values(["symbol", "fy"])
    f["score"] = fn(f)
    f = f[f.score.notna()]
    f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
    # forward-fill latest score per name over calendar
    icd = []
    for fy, gdf in f.groupby("fy"):
        sc, r12 = [], []
        for _, r in gdf.iterrows():
            s = px[r.symbol].dropna()
            a = r.avail
            nx = pd.to_datetime(str(r.fy + 2) + "-07-01")  # when next vintage arrives
            w = s[(s.index >= a)]
            if len(w) < 21:
                continue
            end = min(nx, s.index[-1] + pd.Timedelta(days=1))
            w = w[w.index < end]
            if len(w) < 21:
                continue
            a0 = w.index[0]
            t2 = w.index[-1]
            f12 = w.asof(t2) / w[a0] - 1
            sc.append(r.score); r12.append(f12)
        if len(sc) > 15:
            icd.append((fy, pd.Series(sc).corr(pd.Series(r12), method="spearman"), len(sc)))
    ic = pd.DataFrame(icd, columns=["fy", "ic", "n"]).set_index("fy")
    print(f"== {name}: meanIC={ic.ic.mean():+.4f} IR={ic.ic.mean()/ic.ic.std():+.2f} over {len(ic)} vintages n~{int(ic.n.mean())}")
    print(ic.ic.round(3).to_string())
