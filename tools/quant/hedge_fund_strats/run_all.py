"""Master runner: backtest all hedge fund strategies.

Usage:
    python tools/quant/hedge_fund_strats/run_all.py
    python tools/quant/hedge_fund_strats/run_all.py --tickers 50  # limit universe
    python tools/quant/hedge_fund_strats/run_all.py --quick  # fast run with fewer tickers
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.quant.hedge_fund_strats.core import (
    DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS
)
from tools.quant.hedge_fund_strats.strat_ls_equity import run_long_short_equity, run_ls_variants
from tools.quant.hedge_fund_strats.strat_emn import run_emn
from tools.quant.hedge_fund_strats.strat_global_macro import run_global_macro, run_bridgewater_style
from tools.quant.hedge_fund_strats.strat_merger_arb import run_merger_arb_proxy, run_merger_arb_combined
from tools.quant.hedge_fund_strats.strat_cta import run_cta, run_cta_variants
from tools.quant.hedge_fund_strats.strat_stat_arb import run_stat_arb, run_stat_arb_variants
from tools.quant.hedge_fund_strats.strat_cta_futures import run_cta_futures
from tools.quant.hedge_fund_strats.strat_fi_arb import run_fi_arb
from tools.quant.hedge_fund_strats.strat_credit import run_credit
from tools.quant.hedge_fund_strats.strat_fx_carry import run_fx_carry
from tools.quant.hedge_fund_strats.strat_factor_momentum import run_factor_momentum


def prepare_data(max_tickers: int = None, min_history: int = 1000) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and prepare all data.
    
    Returns:
        (equity_prices, equity_returns, fx_prices, crypto_prices)
    """
    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    # Load equities from twelve_big (has 20-year history)
    print("  Loading equities from twelve_big...")
    equities = DataLoader.load_equities(source="twelve_big", min_rows=min_history)
    
    # Also add polygon_v2 tickers (shorter history, but more names)
    poly_v2_dir = os.path.join(DataLoader.__dict__.get('__qualname__', ''), '..', 'data', 'polygon_v2')
    
    # Filter to tickers with enough history
    if max_tickers and len(equities) > max_tickers:
        # Prefer tickers with longest history
        ticker_lengths = [(t, len(df)) for t, df in equities.items()]
        ticker_lengths.sort(key=lambda x: -x[1])
        keep = [t for t, _ in ticker_lengths[:max_tickers]]
        equities = {t: equities[t] for t in keep}
    
    print(f"  Loaded {len(equities)} equity tickers")
    
    # Build price panel
    print("  Building price panel...")
    prices = DataLoader.build_price_panel(equities)
    
    # Need at least 250 rows (1 year) for meaningful backtest
    # Use data from 2008 onwards (post-GFC for cleaner data)
    prices = prices[prices.index >= "2008-01-01"]
    prices = prices.dropna(how='all')
    
    # Forward fill small gaps
    prices = prices.ffill(limit=5)
    
    # Drop tickers with too many NaNs (>30% missing)
    nan_frac = prices.isna().mean()
    good_tickers = nan_frac[nan_frac < 0.3].index.tolist()
    prices = prices[good_tickers]
    
    print(f"  Price panel: {prices.shape[0]} days x {prices.shape[1]} tickers")
    print(f"  Date range: {prices.index[0].date()} to {prices.index[-1].date()}")
    
    # Returns
    returns = DataLoader.build_return_panel(prices, method="simple")
    
    # Load FX
    print("  Loading FX data...")
    fx_data = DataLoader.load_fx()
    fx_prices = DataLoader.build_price_panel(fx_data) if fx_data else None
    if fx_prices is not None:
        print(f"  FX pairs: {fx_prices.shape[1]}")
    
    # Load crypto
    print("  Loading crypto data...")
    crypto_data = DataLoader.load_crypto()
    crypto_prices = DataLoader.build_price_panel(crypto_data) if crypto_data else None
    if crypto_prices is not None:
        print(f"  Crypto: {crypto_prices.shape[1]}")
    
    return prices, returns, fx_prices, crypto_prices


def run_all_strategies(prices: pd.DataFrame, returns: pd.DataFrame,
                       fx_prices: pd.DataFrame, crypto_prices: pd.DataFrame,
                       quick: bool = False) -> Dict[str, Performance]:
    """Run all 5 hedge fund strategies and return results."""
    
    results = {}
    
    # ---- Strategy 1: Long/Short Equity ----
    try:
        if quick:
            perf, _ = run_long_short_equity(prices, returns,
                                           gross_leverage=1.6, net_exposure=0.625,
                                           n_long=20, n_short=20,
                                           rebalance_freq=21)
            results["L/S 130/30"] = perf
        else:
            ls_results = run_ls_variants(prices, returns)
            results.update({f"L/S {k}": v for k, v in ls_results.items()})
    except Exception as e:
        print(f"  L/S Equity ERROR: {e}")
        import traceback; traceback.print_exc()
    
    # ---- Strategy 2: Equity Market Neutral ----
    try:
        if quick:
            perf, _ = run_emn(prices, returns,
                            n_long=30, n_short=30,
                            gross_leverage=2.0,
                            rebalance_freq=21,
                            beta_neutral=True)
            results["EMN"] = perf
        else:
            perf, _ = run_emn(prices, returns,
                            n_long=40, n_short=40,
                            gross_leverage=2.0,
                            rebalance_freq=21,
                            beta_neutral=True)
            results["EMN"] = perf
    except Exception as e:
        print(f"  EMN ERROR: {e}")
        import traceback; traceback.print_exc()
    
    # ---- Strategy 3: Global Macro ----
    try:
        perf, _ = run_global_macro(prices, returns, fx_prices, crypto_prices)
        results["Global Macro"] = perf
        
        # Bridgewater style risk parity
        if not quick:
            perf_bw = run_bridgewater_style(prices, returns)
            results["Risk Parity (Bridgewater)"] = perf_bw
    except Exception as e:
        print(f"  Global Macro ERROR: {e}")
        import traceback; traceback.print_exc()
    
    # ---- Strategy 4: Merger Arbitrage ----
    try:
        if quick:
            perf, _ = run_merger_arb_proxy(prices, returns, method="pead",
                                           threshold=0.03, holding_period=20)
            results["Merger Arb (PEAD)"] = perf
        else:
            arb_results = run_merger_arb_combined(prices, returns)
            results.update({f"Merger Arb {k}": v for k, v in arb_results.items()})
    except Exception as e:
        print(f"  Merger Arb ERROR: {e}")
        import traceback; traceback.print_exc()
    
    # ---- Strategy 5: Managed Futures / CTA ----
    try:
        if quick:
            perf, _ = run_cta(prices, returns, fx_prices, crypto_prices,
                            target_vol=0.15, rebalance_freq=5)
            results["CTA 15vol"] = perf
        else:
            cta_results = run_cta_variants(prices, returns, fx_prices, crypto_prices)
            results.update({f"CTA {k}": v for k, v in cta_results.items()})
    except Exception as e:
        print(f"  CTA ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 5b: CTA on real futures/macro (Stooq/FRED) ----
    try:
        if not quick:
            perf_f, _ = run_cta_futures(rebalance_freq=21, signal_mode="multi")
            results["CTA Futures (macro 21d)"] = perf_f
    except Exception as e:
        print(f"  CTA Futures ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 6b: Relative Value / Fixed Income Arbitrage ----
    try:
        if not quick:
            perf_fi, _ = run_fi_arb()
            results["FI Arb (curve)"] = perf_fi
    except Exception as e:
        print(f"  FI Arb ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 6c: Credit Strategies (supplementary category) ----
    try:
        if not quick:
            perf_cr, _, _ = run_credit()
            results["Credit (spread z reversion)"] = perf_cr
    except Exception as e:
        print(f"  Credit ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 7: Alternative Risk Premia — FX Carry ----
    try:
        if not quick:
            perf_fx, _ = run_fx_carry()
            results["FX Carry"] = perf_fx
    except Exception as e:
        print(f"  FX Carry ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 8: ARP — Factor Momentum (Fama-French) ----
    try:
        if not quick:
            perf_fm, _ = run_factor_momentum()
            results["Factor Momentum (FF)"] = perf_fm
    except Exception as e:
        print(f"  Factor Momentum ERROR: {e}")
        import traceback; traceback.print_exc()

    # ---- Strategy 6: Relative Value / Statistical Arbitrage ----
    try:
        if quick:
            perf, _ = run_stat_arb(prices, returns,
                                   n_pairs=40, entry_z=1.5, exit_z=0.5,
                                   refit_freq=126, rebalance_freq=5)
            results["StatArb 40pairs"] = perf
        else:
            arb_results = run_stat_arb_variants(prices, returns)
            results.update({f"StatArb {k}": v for k, v in arb_results.items()})
    except Exception as e:
        print(f"  Stat Arb ERROR: {e}")
        import traceback; traceback.print_exc()

    return results


def print_comparison_table(results: Dict[str, Performance]):
    """Print side-by-side comparison of all strategies."""
    print("\n" + "="*70)
    print("COMPARISON TABLE: ALL HEDGE FUND STRATEGIES")
    print("="*70)
    
    headers = ["Strategy", "Ann Return", "Ann Vol", "Sharpe", "Max DD", "Calmar", "Win Rate", "Beta"]
    rows = []
    
    for name, perf in results.items():
        rows.append([
            name,
            f"{perf.annual_return:>8.2%}",
            f"{perf.annual_vol:>8.2%}",
            f"{perf.sharpe:>8.2f}",
            f"{perf.max_drawdown:>8.2%}",
            f"{perf.calmar:>8.2f}",
            f"{perf.win_rate:>8.1%}",
            f"{perf.beta:>8.2f}",
        ])
    
    # Print table
    if not rows:
        print("  No results to display!")
        return
    col_widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(c.ljust(w) for c, w in zip(row, col_widths)))
    
    # Rank by Sharpe
    print("\n  Ranked by Sharpe Ratio:")
    sorted_results = sorted(results.items(), key=lambda x: -x[1].sharpe)
    for i, (name, perf) in enumerate(sorted_results, 1):
        print(f"    {i}. {name:30s}  Sharpe: {perf.sharpe:.2f}  Return: {perf.annual_return:.2%}  MaxDD: {perf.max_drawdown:.2%}")


def export_results(results: Dict[str, Performance], output_dir: str = None):
    """Export results to CSV and save equity curves."""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Summary table
    summary_data = []
    for name, perf in results.items():
        summary_data.append({
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
        })
    
    df = pd.DataFrame(summary_data)
    df.to_csv(os.path.join(output_dir, "strategy_comparison.csv"), index=False)
    print(f"\n  Summary saved to: {os.path.join(output_dir, 'strategy_comparison.csv')}")
    
    # Save equity curves
    for name, perf in results.items():
        if perf.equity_curve is not None:
            safe_name = name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
            perf.equity_curve.to_csv(os.path.join(output_dir, f"equity_{safe_name}.csv"))
    
    print(f"  Equity curves saved to: {output_dir}/")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Backtest hedge fund strategies")
    parser.add_argument("--tickers", type=int, default=None, help="Limit number of tickers")
    parser.add_argument("--quick", action="store_true", help="Quick run with fewer variants")
    parser.add_argument("--cost", type=float, default=TRADING_COST_BPS, help="Trading cost in bps")
    args = parser.parse_args()
    
    t0 = time.time()
    
    # Prepare data
    prices, returns, fx_prices, crypto_prices = prepare_data(max_tickers=args.tickers)
    
    # Run all strategies
    print("\n" + "="*70)
    print("RUNNING ALL STRATEGIES")
    print("="*70)
    
    results = run_all_strategies(prices, returns, fx_prices, crypto_prices, quick=args.quick)
    
    # Print comparison
    print_comparison_table(results)
    
    # Export
    export_results(results)
    
    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"Total elapsed: {elapsed:.1f}s")
    print(f"Strategies run: {len(results)}")
    print(f"Trading cost: {args.cost} bps round-trip")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
