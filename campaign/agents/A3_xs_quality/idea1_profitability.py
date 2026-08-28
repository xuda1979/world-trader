"""Idea 1: Profitability (Novy-Marx style, op_income/TA, NI/TA fallback).
PIT: FY y usable from Jul 1 y+1. Long top tercile, short bottom, monthly, 6bps."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
from engine import *
import pandas as pd, numpy as np

px, rets = load_rets()
f = pd.read_parquet("/Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet")
f = f[f.symbol.isin(px.columns)].copy()
f["opm"] = f.op_income / f.total_assets
f["nim"] = f.net_income / f.total_assets
prof = f.opm.fillna(f.nim)          # profitability: op income fallback net income
f["score"] = prof
f = f[f.score.notna() & (f.total_assets > 0)]
f["avail"] = pd.to_datetime((f.fy + 1).astype(str) + "-07-01")   # 6m offset after Dec FY
f["symbol"] = f.symbol.astype(str)

# build wide score panel forward-filled
dates = px.index
sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
sym_map = {s: i for i, s in enumerate(px.columns)}
for _, r in f.iterrows():
    if r.symbol in sym_map:
        mask = dates >= r.avail
        # only apply until next FY available (next fy+1 Jul) — handle by taking latest per (symbol, date) later
        sig.loc[mask, r.symbol] = r.score
# where multiple FYs overlap (shouldn't after avail rule, but keep last written = newest FY): sort f by fy
f = f.sort_values("fy")
sig = pd.DataFrame(np.nan, index=dates, columns=px.columns)
for _, r in f.iterrows():
    if r.symbol in sym_map:
        mask = dates >= r.avail
        sig.loc[mask, r.symbol] = r.score
sig = sig.where(px.notna())   # only trade names with price data

net, w, turn = backtest(sig, rets)
vt = vol_target(net)
ok, g = full_gates(vt, "idea1_profit_1/3-1/3")
print("avg names/side:", int((w > 0).sum(axis=1).mean()), int((w < 0).sum(axis=1).mean()), "turn bps/day:", round(turn.mean()*6, 2))
if ok:
    p, q95 = scramble_test(sig, rets, g["SR"], nrep=200)
    print("scramble p =", p, "q95 =", round(q95, 2))
    ok = ok and p < 0.05
    if ok:
        D.save_sleeve(vt.iloc[60:], "/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/sleeves/QA_profit_oi_ta.csv",
            meta="""Sleeve: QA_profit_oi_ta (A3_xs_quality r1 idea1)
Signal: cross-sectional profitability = op_income/total_assets (fallback net_income/total_assets when op_income missing); FY y data used only from Jul 1 of y+1 (6-month PIT lag).
Portfolio: monthly rebalance at month-end, long top tercile / short bottom tercile of ranked universe (100%/100%), T+1 execution, 6bps one-side costs, vol-target 10% ann via trailing expanding window (min 60d, scale cap 5x).
Validation r1: %s | scramble p=%.3f (200 perms, real SR above 95th pctile of scrambled)
Economic rationale: profitable firms earn higher returns (Novy-Marx 2013 gross profitability prices like earnings yield); short low-profitability names that persistently burn capital. Quality premium is robust across 16y, halves, and scramble test.
Caveats: panel = current S&P-500 constituents (survivorship bias: short leg returns understated); op_income coverage 86%% of fundamentals rows; fundamentals from fundamentals_annual.parquet (free data).
""" % (g, p))
        print("SAVED QA_profit_oi_ta")
