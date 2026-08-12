"""Run new-category strategies and append to results without rerunning all.

Runs:
  1. Relative Value / Statistical Arbitrage variants (real data)
  2. Multi-Strategy blend (equal-weight of L/S 130/30 + CTA + Global Macro + StatArb)
     -> demonstrates the 'low-correlation streams' claim of multi-strategy funds

Appends rows to results/strategy_comparison.csv and saves equity curves.
"""

import sys, os
import numpy as np
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.quant.hedge_fund_strats.core import (
    DataLoader, BacktestEngine, compute_performance, TRADING_COST_BPS
)
from tools.quant.hedge_fund_strats.strat_stat_arb import run_stat_arb_variants

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_data():
    print("\n" + "=" * 70)
    print("LOADING DATA")
    print("=" * 70)
    equities = DataLoader.load_equities(source="twelve_big", min_rows=1000)
    prices = DataLoader.build_price_panel(equities)
    prices = prices[prices.index >= "2008-01-01"].dropna(how='all')
    prices = prices.ffill(limit=5)
    nan_frac = prices.isna().mean()
    prices = prices[nan_frac[nan_frac < 0.3].index.tolist()]
    returns = DataLoader.build_return_panel(prices, method="simple")
    print(f"  Price panel: {prices.shape[0]}d x {prices.shape[1]} tickers")
    return prices, returns


def perf_from_curve(curve_csv):
    eq = pd.read_csv(curve_csv, index_col=0, parse_dates=True).iloc[:, 0]
    rets = eq.pct_change().dropna()
    perf = compute_performance(rets, eq, benchmark_returns=None)
    return perf


def append_row(name, perf, df_out):
    row = {
        'strategy': name,
        'total_return': perf.total_return,
        'annual_return': perf.annual_return,
        'annual_vol': perf.annual_vol,
        'sharpe': perf.sharpe,
        'sortino': perf.sortino,
        'max_drawdown': perf.max_drawdown,
        'calmar': perf.calmar,
        'win_rate': perf.win_rate,
        'profit_factor': perf.profit_factor,
        'beta': perf.beta,
        'alpha': perf.alpha,
        'information_ratio': perf.information_ratio,
        'skewness': perf.skewness,
        'kurtosis': perf.kurtosis,
        'var_95': perf.var_95,
        'cvar_95': perf.cvar_95,
        'n_trades': perf.n_trades,
        'turnover_annual': perf.turnover_annual,
    }
    df_out = pd.concat([df_out, pd.DataFrame([row])], ignore_index=True)
    return df_out


def main():
    prices, returns = load_data()

    df_out = pd.read_csv(RESULTS_DIR / "strategy_comparison.csv")

    # ---- 1. Stat Arb variants ----
    print("\n" + "=" * 70)
    print("RELATIVE VALUE / STAT ARB")
    print("=" * 70)
    results = run_stat_arb_variants(prices, returns)
    for name, perf in results.items():
        df_out = append_row("StatArb " + name, perf, df_out)
        # Variant keys already carry the StatArb_ prefix; strip it for the
        # curve filename so the blend's lookup (equity_StatArb_40pairs_z15.csv)
        # matches.
        safe = name.replace("StatArb_", "").replace("/", "_").replace(" ", "_")
        perf.equity_curve.to_csv(RESULTS_DIR / f"equity_StatArb_{safe}.csv")

    # ---- 2. Multi-Strategy blend ----
    print("\n" + "=" * 70)
    print("MULTI-STRATEGY BLEND (equal weight)")
    print("=" * 70)
    # Candidate curve files per stream (quick-run vs full-run naming);
    # futures CTA preferred when present (real managed-futures universe).
    candidates = {
        "ls": ["equity_L_S_130_30.csv"],
        "cta": ["equity_CTA_Futures_multi_21d.csv", "equity_CTA_15vol.csv", "equity_CTA_CTA_15vol_21d.csv"],
        "macro": ["equity_Global_Macro.csv"],
    }
    streams = {}
    for key, names in candidates.items():
        for nm in names:
            path = RESULTS_DIR / nm
            if path.exists():
                eq = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
                streams[key] = eq.pct_change()
                print(f"  {key}: {nm} ({len(eq)} rows)")
                break
    if not streams:
        print("  No equity curves found for blend; run full suite first.")
        df_out.to_csv(RESULTS_DIR / "strategy_comparison.csv", index=False)
        return

    # Include stat arb stream if present
    sa_path = RESULTS_DIR / "equity_StatArb_40pairs_z15.csv"
    if sa_path.exists():
        eq = pd.read_csv(sa_path, index_col=0, parse_dates=True).iloc[:, 0]
        streams["statarb"] = eq.pct_change()
        print(f"  statarb: {sa_path.name}")

    blend = pd.concat(streams, axis=1).mean(axis=1).dropna()
    equity = (1 + blend).cumprod()
    perf = compute_performance(blend, equity, benchmark_returns=None)
    df_out = append_row("Multi-Strategy EW", perf, df_out)
    perf.equity_curve.to_csv(RESULTS_DIR / "equity_Multi_Strategy_EW.csv")

    # Blend corr matrix (why multi-strategy works: low cross-correlation)
    corr = pd.concat(streams, axis=1).corr()
    print("\n  Stream correlation matrix:")
    print(corr.round(3).to_string())

    df_out.to_csv(RESULTS_DIR / "strategy_comparison.csv", index=False)
    print(f"\n  Appended results -> {RESULTS_DIR / 'strategy_comparison.csv'}")


if __name__ == "__main__":
    main()
