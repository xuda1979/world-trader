#!/usr/bin/env python3
"""Explore which blend convention reproduces equity_Multi_Strategy_SharpeW.csv."""
import itertools
import sys

import numpy as np
import pandas as pd

RES = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/results"
STREAMS = {
    "ls": "equity_L_S_130_30.csv",
    "cta": "equity_CTA_Futures_multi_21d.csv",
    "macro": "equity_Global_Macro.csv",
    "statarb": "equity_StatArb_40pairs_z15.csv",
    "rp": "equity_Risk_Parity_Bridgewater.csv",
    "fx": "equity_FX_Carry.csv",
}

eqs = {}
for k, f in STREAMS.items():
    s = pd.read_csv(f"{RES}/{f}", index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    eqs[k] = s

committed = pd.read_csv(f"{RES}/equity_Multi_Strategy_SharpeW.csv",
                        index_col=0, parse_dates=True).iloc[:, 0].astype(float)
print("committed index:", committed.index.min().date(), committed.index.max().date(),
      "n=", len(committed), "dup?", committed.index.duplicated().any())
dow = pd.Series(committed.index.dayofweek).value_counts().sort_index()
print("committed DOW hist:", dict(dow))

rets = {k: eq.pct_change() for k, eq in eqs.items()}


def geom_sharpe(r, rf=0.02):
    g = np.log1p(r.dropna())
    if len(g) < 10 or g.std() == 0:
        return np.nan
    return (g.mean() * 252 - rf) / (g.std() * np.sqrt(252))


# ---- convention grid: how returns are aligned + whether weights use rf
conventions = []
for join in ("outer", "committed_index"):
    for fill in ("zero", "ffill_pct"):
        for rf in (0.0, 0.02):
            conventions.append((join, fill, rf))

best = None
for join, fill, rf in conventions:
    if join == "outer":
        R = pd.DataFrame({k: v for k, v in rets.items()})
    else:
        R = pd.DataFrame({k: v.reindex(committed.index) for k, v in rets.items()})
    if fill == "zero":
        R = R.fillna(0.0)
    else:
        R = R.ffill().fillna(0.0)
    srs = {k: geom_sharpe(R[k], rf) for k in R.columns}
    w = pd.Series(srs).clip(lower=0.05)
    w = w / w.sum()
    port = (R * w).sum(axis=1)
    eq_b = (1 + port).cumprod()
    if join == "outer":
        j = pd.concat([eq_b.rename("b"), committed.rename("c")], axis=1, join="inner").dropna()
    else:
        j = pd.concat([eq_b.rename("b"), committed.rename("c")], axis=1).dropna()
    if len(j) < 100:
        print(f"{join}/{fill}/rf={rf}: overlap {len(j)} too small")
        continue
    dev = (j.b - j.c).abs().max()
    print(f"{join:15s}/{fill:10s}/rf={rf}: n={len(j)} maxdev={dev:.6g} weights="
          + "{" + ", ".join(f"{k}:{v:.2f}" for k, v in w.items()) + "}")
    if best is None or dev < best[0]:
        best = (dev, join, fill, rf, w)
print("\nBEST:", best[:4])
print(best[4])
