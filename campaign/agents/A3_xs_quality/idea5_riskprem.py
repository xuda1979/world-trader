"""Idea 5 (family-4 other side): long high beta/corr/downside blend. Full gates."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from engine import *
import pandas as pd, numpy as np

px, rets = load_rets()
feat = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/daily_features.parquet")
feat["date"] = pd.to_datetime(feat["date"])
feat = feat[feat.symbol.isin(px.columns)]

def build(col):
    w = feat.pivot_table(index="date", columns="symbol", values=col).reindex(columns=px.columns)
    pos = w.index.searchsorted(px.index, side="right") - 1
    ok = pos >= 0
    sig = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    sig.loc[ok, :] = w.iloc[pos[ok]].values
    return sig.where(px.notna())

parts = [build("beta_12m"), build("corr_6m"), build("downside_6m")]
zs = [ (p.sub(p.mean(axis=1), axis=0)).div(p.std(axis=1), axis=0) for p in parts ]
sig = sum(z for z in zs) / 3.0
print("names/ME median:", int(sig.notna().sum(axis=1).median()))

def run(sig, lf, sf, tag):
    net, w, turn = backtest(sig, rets, long_frac=lf, short_frac=sf)
    start = sig.dropna(how="all").index[0]
    rr = strategy_ret(net, start)
    ok, g = full_gates(rr, tag)
    return ok, g, rr

ok, g, v = run(sig, 1/3, 1/3, "idea5_riskblend 1/3-1/3")
if not ok:
    ok2, g2, _ = run(sig, 0.2, 0.2, "idea5_riskblend 20/20")
    ok3, g3, _ = run(sig, 0.4, 0.4, "idea5_riskblend 40/40")
    best = max([(ok,g),(ok2,g2),(ok3,g3)], key=lambda x: x[1]["SR"])
    ok, g = best
print("BEST:", ok, g)
if ok:
    start = sig.dropna(how="all").index[0]
    p, q = scramble_test(sig, rets, g["SR"], start=start)
    print("scramble p:", p)
    ok &= p < 0.05
    if ok:
        D.save_sleeve(v, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_risk_premium_blend.csv", meta=f"risk blend {g} p={p}")
        print("SAVED")
