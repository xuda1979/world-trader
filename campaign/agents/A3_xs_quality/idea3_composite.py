"""Idea 3: Composite quality z(avg(profitability, low leverage, ROE stability)), PIT 6m."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from engine import *
import pandas as pd, numpy as np

px, rets = load_rets()
f = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")
f = f[f.symbol.isin(px.columns)].copy().sort_values(["symbol", "fy"])
f["prof"] = (f.op_income/f.total_assets).fillna(f.net_income/f.total_assets)
f["lev"] = f.debt / (f.debt.abs() + f.equity.abs())          # 0..1, lower better
f["roe"] = f.net_income / f.equity.replace(0, np.nan)
f["roe_sd"] = f.groupby("symbol").roe.transform(lambda s: s.rolling(5, min_periods=3).std())
f["score"] = (f.prof.rank(pct=True)
              + (1 - f.lev.clip(0, 1)).where(f.lev.notna(), np.nan).rank(pct=True)
              + (-f.roe_sd).rank(pct=True)) / 3.0
f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
f = f[f.score.notna()].sort_values("fy")
dates = px.index
sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
for _, r in f.iterrows():
    sig.loc[dates >= r.avail, r.symbol] = r.score
sig = sig.where(px.notna())
print("median names with score per ME:", int(sig.notna().sum(axis=1).median()))
net, w, turn = backtest(sig, rets)
vt = vol_target(net)
ok, g = full_gates(vt, "idea3_composite")
mes = [d for d in month_ends(px) if d in dates]
ics = {}
for t, t1 in zip(mes[:-1], mes[1:]):
    s = sig.loc[t].dropna()
    if len(s) < 20: continue
    fwd = px.loc[t1]/px.loc[t]-1
    com = s.index.intersection(fwd.dropna().index)
    ics[t] = s[com].rank().corr(fwd[com].rank())
ics = pd.Series(ics)
print("mean IC:", round(ics.mean(),4), "ICIR:", round(ics.mean()/ics.std()*np.sqrt(12),2))
