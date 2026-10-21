"""Idea 2: Investment factor (Cooper et al): short high asset growth, long low.
PIT lag 6m. Terciles + 130/30 variants."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from engine import *
import pandas as pd, numpy as np

px, rets = load_rets()
f = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")
f = f[f.symbol.isin(px.columns)].copy()
f = f.sort_values(["symbol", "fy"])
f["ta_prev"] = f.groupby("symbol").total_assets.shift(1)
f["ag"] = f.total_assets / f.ta_prev - 1.0
f["score"] = -f.ag                      # low growth = long
f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")
f = f[f.score.notna() & (f.ta_prev > 0)].sort_values("fy")

dates = px.index
sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
for _, r in f.iterrows():
    sig.loc[dates >= r.avail, r.symbol] = r.score
sig = sig.where(px.notna())

net, w, turn = backtest(sig, rets)
vt = vol_target(net)
ok, g = full_gates(vt, "idea2_invest_tercile")
if ok:
    p, q = scramble_test(sig, rets, g["SR"]); print("scramble p:", p)
    ok &= p < 0.05
if ok:
    D.save_sleeve(vt.iloc[60:], "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_inv_growth.csv")
else:
    # try 130/30 style: long top 20% short bottom 20%, and zscore version
    net2, _, _ = backtest(sig, rets, long_frac=0.2, short_frac=0.2)
    vt2 = vol_target(net2)
    ok2, g2 = full_gates(vt2, "idea2_invest_20/20")
    print("20/20 variant gates:", ok2)
    # IC diagnostic
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
