"""Raw annual IC of fundamental scores vs fwd 12m returns, by FUNDAMENTAL VINTAGE."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
import numpy as np, pandas as pd

px, rets = load_panel()
F = pd.read_parquet(FUND)
F = F[F.symbol.isin(px.columns)].copy()
F["avail"] = pd.to_datetime((F.fy + 1).astype(str) + "-07-01")

def zsc(f, x):
    med = x.groupby(f["fy"]).transform("median")
    sd = x.groupby(f["fy"]).transform(lambda s: s.std())
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

def score_growth(f):
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    d_rev = (f2.revenue - g.revenue.shift(1)) / f2.total_assets.where(lambda s: s > 0)
    d_oi = (f2.op_income - g.op_income.shift(1)) / f2.total_assets.where(lambda s: s > 0)
    legs = pd.DataFrame({"d_rev": d_rev, "d_oi": d_oi})
    out = pd.Series(np.nan, index=f2.index)
    for c in legs.columns:
        out = out.add(zsc(f2, legs[c]), fill_value=0)
    n = legs.notna().sum(axis=1)
    return (out / n.where(n > 0)).where(n > 0), f2

def score_accrual(f):
    # Sloan (1996): low accruals = long. accrual = (dWC - dep)/TA ; proxy: (NI - OCF)/TA; no CF stmt.
    # use delta WC proxy: (dReceivables + dInventory - dPayables - dDepAmort?) / TA
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    drec = (f2.receivables - g.receivables.shift(1))
    dinv = (f2.inventory - g.inventory.shift(1))
    dpay = (f2.payables - g.payables.shift(1))
    acc = (drec + dinv - dpay) / f2.total_assets.where(lambda s: s > 0)
    return -zsc(f2, acc), f2   # short high accrual

def score_agroup(f):
    # asset growth (Cooper): short high asset growth
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    ag = f2.total_assets / g.total_assets.shift(1) - 1
    return -zsc(f2, ag), f2

def score_leverage(f):
    lev = (f.debt - f.cash) / f.total_assets.where(lambda s: s > 0)
    return -zsc(f, lev), f

def score_piotroski(f):
    # simplified F-score legs with available fields
    f2 = f.sort_values(["symbol", "fy"]).copy()
    g = f2.groupby("symbol")
    roa = f2.net_income / f2.total_assets.where(lambda s: s > 0)
    cfo = f2.op_income / f2.total_assets.where(lambda s: s > 0)  # proxy
    d_roa = roa - g.apply(lambda x: (x.net_income / x.total_assets.where(lambda s: s > 0)).shift(1))
    acc = (drec := None)  # placeholder
    legs = pd.DataFrame({
        "roa": roa > 0, "cfo": cfo > 0, "d_roa": d_roa > 0,
        "eq_iss": -(f2.shares - g.shares.shift(1)).fillna(0) > 0,
    }).astype(float)
    legs = legs.where(f2.net_income.notna() & f2.total_assets.notna())
    return legs.sum(axis=1).where(f2.net_income.notna()), f2

SCORES = {
    "value": (score_value, None), "prof": (score_prof, None),
    "growth": (lambda f: score_growth(f)[0], None),
    "accrual_inv": (lambda f: score_accrual(f)[0], None),
    "asset_growth_inv": (lambda f: score_agroup(f)[0], None),
    "leverage_inv": (lambda f: score_leverage(f)[0], None),
    "piotroski": (lambda f: score_piotroski(f)[0], None),
}

for name, (fn, _) in SCORES.items():
    try:
        f = F.copy()
        f["score"] = fn(f)
        f = f[f.score.notna() & (f.total_assets.notna())]
        icd = []
        for fy, g in f.groupby("fy"):
            sc, ret12 = [], []
            for _, r in g.iterrows():
                if r.symbol not in px.columns:
                    continue
                s = px[r.symbol].dropna()
                s = s[(s.index >= r.avail) & (s.index <= pd.Timestamp(str(r.fy + 2) + "-06-30"))]
                if len(s) < 21:
                    continue
                a = s.index[0]
                t2 = pd.Timestamp(str(r.fy + 2) + "-06-30")   # window end
                if t2 > s.index[-1]:
                    continue
                f12 = s.asof(t2) / s[a] - 1
                sc.append(r.score); ret12.append(f12)
            if len(sc) > 15:
                icd.append((fy, pd.Series(sc).corr(pd.Series(ret12), method="spearman"), len(sc)))
        ic = pd.DataFrame(icd, columns=["fy", "ic", "n"]).set_index("fy")
        print(f"\n== {name}: meanIC={ic.ic.mean():+.4f} IR={ic.ic.mean()/ic.ic.std():+.2f} over {len(ic)} vintages")
        print(ic.ic.round(3).to_string())
    except Exception as e:
        import traceback; traceback.print_exc()
