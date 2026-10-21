#!/usr/bin/env python3
"""Explore round 2: core.py-style arithmetic Sharpe (excess mean / sd * sqrt252), plus
subperiod weight options, outer-join with per-stream dropna, and window variants."""
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
rets = {k: eq.pct_change() for k, eq in eqs.items()}


def sharpe_core(r, rf=0.02):
    r = r.dropna()
    if len(r) < 10 or r.std() == 0:
        return np.nan
    excess = r - rf / 252
    return excess.mean() / r.std() * np.sqrt(252)


def build(mode, rf=0.02):
    if mode == "outer_na":
        R = pd.DataFrame(rets)  # outer join, NaN where missing
        srs = {k: sharpe_core(R[k].dropna(), rf) for k in R.columns}
    elif mode == "committed_na":
        R = pd.DataFrame({k: v.reindex(committed.index) for k, v in rets.items()})
        srs = {k: sharpe_core(R[k].dropna(), rf) for k in R.columns}
    elif mode == "arith_outer":  # arithmetic (non-geometric) excess sharpe, no sqrt252 on mean
        R = pd.DataFrame(rets)
        srs = {k: (R[k].dropna().mean() - rf / 252) / R[k].dropna().std() for k in R.columns}
    w = pd.Series(srs).clip(lower=0.05)
    w = w / w.sum()
    port = (R.fillna(0.0) * w).sum(axis=1)
    return w, (1 + port).cumprod()


for mode in ("outer_na", "committed_na", "arith_outer"):
    w, eqb = build(mode)
    j = pd.concat([eqb.rename("b"), committed.rename("c")], axis=1, join="inner").dropna()
    dev = (j.b - j.c).abs().max()
    print(f"{mode:14s}: n={len(j)} maxdev={dev:.6g}  w=" +
          "{" + ", ".join(f"{k}:{v:.3f}" for k, v in w.items()) + "}")

# maybe weights are renormalized over non-missing each day, or the portfolio starts at
# FX_Carry's start (2019). Try: portfolio only over common window (all 6 live)
R = pd.DataFrame(rets).dropna()
print("\ncommon-window (all 6 live):", R.index.min().date(), "..", R.index.max().date(), "n=", len(R))
for rf in (0.0, 0.02):
    srs = {k: sharpe_core(R[k], rf) for k in R.columns}
    w = pd.Series(srs).clip(lower=0.05)
    w /= w.sum()
    port = (R * w).sum(axis=1)
    eqb = (1 + port).cumprod()
    j = pd.concat([eqb.rename("b"), committed.reindex(R.index).rename("c")], axis=1).dropna()
    dev = (j.b - j.c).abs().max()
    print(f"  common rf={rf}: maxdev={dev:.6g}  w=" +
          "{" + ", ".join(f"{k}:{v:.3f}" for k, v in w.items()) + "}")

# check whether committed curve's daily returns equal a fixed-weight blend on ANY subwindow:
# regress committed pct_change on stream returns over the FX window (2019+)
c = committed.pct_change().dropna()
X = pd.DataFrame({k: rets[k] for k in STREAMS}).reindex(c.index).fillna(0.0)
coef, res_, rank, sv = np.linalg.lstsq(X.values, c.values, rcond=None)
pred = pd.Series(X.values @ coef, index=c.index)
print("\nLS-coef (unconstrained, daily):", dict(zip(STREAMS, np.round(coef, 4))))
print("R^2:", round(1 - ((c - pred) ** 2).sum() / ((c - c.mean()) ** 2).sum(), 4))
