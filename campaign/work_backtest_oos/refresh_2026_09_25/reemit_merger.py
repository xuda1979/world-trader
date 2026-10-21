#!/usr/bin/env python3
"""2026-09-25 Merger_Arb_PEAD_5pct re-emit on fresh twelve_big data.

Chain (verified): DataLoader.load_equities(twelve_big, min_rows=1000) -> build_price_panel ->
2008+ -> ffill(5) -> drop >30% NaN tickers -> compute_pead_signals(threshold=0.05, win 3, hold 20)
-> BacktestEngine.run_signal_based @ 12bps RT -> equity curve -> library ret = curve.pct_change().

Steps:
  1. Rebuild on CURRENT data; byte-verify overlap vs committed library CSV (gate).
  2. Extend committed library CSV append-only.
  3. Also extend the tools/quant/hedge_fund_strats/results/equity_Merger_Arb_PEAD_5pct.csv
     (same rows; source of the library conversion).
"""
import sys, os
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/tools")
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant")
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
LIB = f"{ROOT}/campaign/results/sleeve_library/Merger_Arb_PEAD_5pct.csv"
EQ = f"{ROOT}/tools/quant/hedge_fund_strats/results/equity_Merger_Arb_PEAD_5pct.csv"

from hedge_fund_strats.core import DataLoader, BacktestEngine
from hedge_fund_strats.strat_merger_arb import compute_pead_signals

def build():
    # load_equities skips non-CSV-schema files defensively: filter out manifest.csv explicitly
    import glob, os
    import pandas as pd
    d = f"{ROOT}/tools/quant/data/twelve_big"
    eq = {}
    for f in sorted(glob.glob(os.path.join(d, "*.csv"))):
        if os.path.basename(f) == "manifest.csv":
            continue
        ticker = os.path.basename(f).replace(".csv", "")
        df = pd.read_csv(f, parse_dates=["date"], index_col="date")
        if len(df) < 1000:
            continue
        eq[ticker] = df
    prices = DataLoader.build_price_panel(eq)
    prices = prices[prices.index >= "2008-01-01"].dropna(how="all")
    prices = prices.ffill(limit=5)
    nf = prices.isna().mean()
    prices = prices[nf[nf < 0.3].index.tolist()]
    returns = DataLoader.build_return_panel(prices, method="simple")
    signals = compute_pead_signals(returns, prices, 3, 20, threshold=0.05)
    engine = BacktestEngine(prices, cost_bps=12.0)
    daily_ret, equity, turnover, n_trades = engine.run_signal_based(signals, holding_period=20)
    ret = equity.pct_change().dropna()
    return ret

def main():
    ret = build()
    lib = pd.read_csv(LIB, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([ret.rename("c"), lib.rename("m")], axis=1, join="inner").dropna()
    dev = (j.c - j.m).abs()
    maxdev = float(dev.max()) if len(j) else float("nan")
    print(f"overlap n={len(j)} maxdev={maxdev:.3e} committed_last={lib.index.max().date()} cand_last={ret.index.max().date()}")
    # body must be byte-exact; deviations allowed ONLY in the last committed row (build-time
    # last-bar marking / tiny provider revision), which is revalued from current data.
    body = dev[dev.index < lib.index.max()]
    tail = dev[dev.index == lib.index.max()]
    if float(body.max()) > 1e-9:
        print("BODY MISMATCH — not extending")
        sys.exit(1)
    out = lib.copy()
    if len(tail) and float(tail.max()) > 1e-9:
        print(f"revaluing last committed row {lib.index.max().date()}: {float(lib.iloc[-1]):.6f} -> {float(ret.loc[lib.index.max()]):.6f}")
        out.iloc[-1] = float(ret.loc[lib.index.max()])
    new = ret[ret.index > lib.index.max()]
    if len(new):
        out = pd.concat([out, new])
        out.index.name = "date"
        out.to_frame("ret").to_csv(LIB)
        print(f"library extended -> {out.index.max().date()} (+{len(new)} rows)")
    else:
        out.index.name = "date"
        out.to_frame("ret").to_csv(LIB)
        print("no new rows (tail revalued only)")
    # results/ file: same ret series under its own name
    eqc = pd.read_csv(EQ, index_col=0, parse_dates=True).iloc[:, 0]
    new_eq = ret[ret.index > eqc.index.max()]
    if len(new_eq):
        out2 = pd.concat([eqc, new_eq])
        out2.index.name = "date"
        out2.to_frame("ret").to_csv(EQ)
        print(f"results file extended -> {out2.index.max().date()} (+{len(new_eq)} rows)")

if __name__ == "__main__":
    main()
