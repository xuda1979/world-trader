"""Quick monthly IC check for fundamental scores on union panel (with market-control)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_FUNDAMENTAL/scratch")
from hf_engine import *
import numpy as np, pandas as pd

px, rets = load_panel()
F = pd.read_parquet(FUND)
F = F[F.symbol.isin(px.columns)].copy()
F["avail"] = pd.to_datetime((F.fy + 1).astype(str) + "-07-01")

# forward month returns per (symbol, avail-vintage)
rows = []
for _, r in F.iterrows():
    if r.symbol not in px.columns:
        continue
    s = px[r.symbol].dropna()
    s = s[(s.index >= r.avail) & (s.index <= pd.Timestamp(str(r.fy + 2) + "-06-30"))]
    if len(s) < 20:
        continue
    # month-end to month-end fwd returns
    me = s.groupby([s.index.year, s.index.month]).max()
    fwd = s.shift(-1) / s - 1
    for t in me.values:
        if t in s.index:
            rows.append((r.symbol, t, r.score_raw if False else None))

def score_value(f):
    eb = f.net_income / f.equity.replace(0, np.nan)
    ic = (f.equity + f.debt - f.cash).where(lambda s: s > 0)
    oic = f.op_income / ic
    sta = f.revenue / f.total_assets.where(lambda s: s > 0)
    df = pd.DataFrame({"eb": eb, "oic": oic, "sta": sta})
    out = pd.Series(np.nan, index=f.index)
    for c in df.columns:
        x = df[c]
        med = x.groupby(f["fy"]).transform("median")
        sd = x.groupby(f["fy"]).transform(lambda s: s.std())
        zx = ((x - med) / sd.where(sd > 0)).clip(-3, 3)
        out = out.add(zx, fill_value=0)
    nlegs = df.notna().sum(axis=1)
    return (out / nlegs.where(nlegs > 0)).where(nlegs > 0)

def score_prof(f):
    oi = f.op_income / f.total_assets.where(lambda s: s > 0)
    ni = f.net_income / f.total_assets.where(lambda s: s > 0)
    df = pd.DataFrame({"oi": oi, "ni": ni})
    out = pd.Series(np.nan, index=f.index)
    for c in df.columns:
        x = df[c]
        med = x.groupby(f["fy"]).transform("median")
        sd = x.groupby(f["fy"]).transform(lambda s: s.std())
        zx = ((x - med) / sd.where(sd > 0)).clip(-3, 3)
        out = out.add(zx, fill_value=0)
    nlegs = df.notna().sum(axis=1)
    return (out / nlegs.where(nlegs > 0)).where(nlegs > 0)

rets_m = rets.resample('ME').prod()
mkt_m = rets.mean(axis=1).resample('ME').prod()   # EW market monthly

for name, fn in [("value", score_value), ("prof", score_prof)]:
    f = F.copy()
    f["score"] = fn(f)
    f = f[f.score.notna()]
    ics, ics_n = [], []
    # for each vintage month: rank corr of score vs fwd 12m return, demeaned market
    for _, r in f.iterrows():
        s = px[r.symbol].dropna()
        s = s[(s.index >= r.avail) & (s.index <= pd.Timestamp(str(r.fy + 2) + "-06-30"))]
        if len(s) < 21:
            continue
        # fwd 12m return from avail
        a = s.index[0]
        if a + pd.Timedelta(days=365) <= s.index[-1]:
            f12 = s[a + pd.Timedelta(days=365)] / s[a] - 1
            rows.append((name, r.fy, r.score, f12))
    d = pd.DataFrame(rows, columns=["name", "fy", "score", "f12"])
    d = d.dropna()
    # per-fy rank IC
    ic_by_fy = d.groupby("fy").apply(lambda g: g.score.corr(g.f12, method="spearman") if len(g) > 15 else np.nan)
    icm = ic_by_fy.mean()
    print(f"{name}: mean fy-level rankIC(score, fwd12m) = {icm:.4f} over {ic_by_fy.notna().sum()} vintages, IR={icm/ic_by_fy.std():.2f}")
    print(ic_by_fy.round(3).to_string())
