"""Strategy 1: Long/Short Equity (L/S)

Classic hedge fund strategy (Alfred Winslow Jones, 1949).
Dollar-neutral or beta-adjusted: long undervalued, short overvalued.

Signal: Cross-sectional momentum + reversal composite
  - Medium-term momentum (6-12 months, skip 1 month)
  - Short-term reversal (1-5 days)
  - Volatility-adjusted position sizing

Variants:
  - 130/30 (130% long, 30% short, 100% net)
  - 100/0 (100% long only, no short)
  - Market neutral (dollar neutral)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from .core import DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS


def compute_ls_signals(prices: pd.DataFrame,
                       returns: pd.DataFrame,
                       mom_lookback: int = 252,
                       mom_skip: int = 21,
                       reversal_lookback: int = 5,
                       vol_window: int = 60,
                       n_long: int = 30,
                       n_short: int = 30) -> pd.DataFrame:
    """Compute Long/Short equity signals.
    
    Combines:
      - Medium-term momentum (12-month minus 1-month return)
      - Short-term reversal (5-day return, negated)
      - Volatility normalization
    
    Returns target weights DataFrame[T, N].
    """
    # Momentum: 12-month return skipping last month
    mom = prices.shift(mom_skip) / prices.shift(mom_lookback + mom_skip) - 1
    
    # Reversal: 5-day return (negated for contrarian)
    rev = -(prices / prices.shift(reversal_lookback) - 1)
    
    # Volatility for normalization
    vol = returns.rolling(vol_window).std()
    vol = vol.replace(0, np.nan)
    
    # Normalize signals by volatility
    mom_vol_adj = mom / vol
    rev_vol_adj = rev / vol
    
    # Cross-sectional rank (uniform [-1, 1])
    mom_rank = mom_vol_adj.rank(axis=1, pct=True).sub(0.5).mul(2)
    rev_rank = rev_vol_adj.rank(axis=1, pct=True).sub(0.5).mul(2)
    
    # Composite: 70% momentum + 30% reversal
    composite = 0.7 * mom_rank + 0.3 * rev_rank
    
    # Select top/bottom n stocks each day
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    
    for i in range(len(composite)):
        row = composite.iloc[i].dropna()
        if len(row) < n_long + n_short:
            continue
        
        longs = row.nlargest(n_long).index
        shorts = row.nsmallest(n_short).index
        
        # Volatility-adjusted weights
        vol_row = vol.iloc[i]
        inv_vol_long = 1 / vol_row[longs]
        inv_vol_short = 1 / vol_row[shorts]

        # Normalize to target exposure (use .loc to avoid chained indexing)
        date = prices.index[i]
        weights.loc[date, longs] = (inv_vol_long / inv_vol_long.sum()).values
        weights.loc[date, shorts] = (-inv_vol_short / inv_vol_short.sum()).values
    
    return weights


def run_long_short_equity(prices: pd.DataFrame,
                          returns: pd.DataFrame,
                          gross_leverage: float = 1.0,
                          net_exposure: float = 0.3,
                          n_long: int = 30,
                          n_short: int = 30,
                          rebalance_freq: int = 21,
                          cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    """Run Long/Short Equity backtest.
    
    Args:
        gross_leverage: total gross exposure (long + short)
        net_exposure: net long exposure (long - short) / gross
        n_long: number of long positions
        n_short: number of short positions
        rebalance_freq: rebalance every N days
        cost_bps: round-trip trading cost in bps
    """
    print("\n" + "="*70)
    print("STRATEGY 1: LONG/SHORT EQUITY")
    print("="*70)
    print(f"  Gross leverage: {gross_leverage:.0%}")
    print(f"  Net exposure:   {net_exposure:+.0%}")
    print(f"  Long positions: {n_long}")
    print(f"  Short positions: {n_short}")
    print(f"  Rebalance: every {rebalance_freq} days")
    print(f"  Cost: {cost_bps} bps round-trip")
    
    # Compute signals
    print("  Computing signals...")
    weights = compute_ls_signals(prices, returns, n_long=n_long, n_short=n_short)
    
    # Scale to target gross/net exposure
    # Long weight = gross * (1 + net) / 2
    # Short weight = gross * (1 - net) / 2
    long_scale = gross_leverage * (1 + net_exposure) / 2
    short_scale = gross_leverage * (1 - net_exposure) / 2
    
    # Scale positive and negative weights
    for i in range(len(weights)):
        row = weights.iloc[i].copy()
        pos_idx = row[row > 0].index
        neg_idx = row[row < 0].index
        pos = row[pos_idx]
        neg = row[neg_idx]
        date = weights.index[i]
        if len(pos) > 0:
            weights.loc[date, pos_idx] = (pos / pos.sum() * long_scale).values
        if len(neg) > 0:
            weights.loc[date, neg_idx] = (neg / neg.abs().sum() * short_scale * -1).values
    
    # Run backtest
    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=rebalance_freq)
    
    # Benchmark: SPY buy and hold
    spy_col = "SPY" if "SPY" in returns.columns else None
    bench = returns[spy_col] if spy_col else returns.mean(axis=1)
    
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=int(turnover / 2),
                               turnover_total=turnover)
    
    print(f"\n  Results:")
    print(perf.summary())
    
    return perf, weights


def run_ls_variants(prices: pd.DataFrame, returns: pd.DataFrame) -> Dict[str, Performance]:
    """Run multiple L/S variants."""
    results = {}
    
    # 130/30 (classic hedge fund)
    perf, _ = run_long_short_equity(prices, returns,
                                     gross_leverage=1.6, net_exposure=0.625,
                                     n_long=30, n_short=30)
    results["130/30"] = perf
    
    # 100% net (long-biased)
    perf, _ = run_long_short_equity(prices, returns,
                                     gross_leverage=1.2, net_exposure=0.833,
                                     n_long=40, n_short=10)
    results["120/20"] = perf
    
    # Market neutral
    perf, _ = run_long_short_equity(prices, returns,
                                     gross_leverage=2.0, net_exposure=0.0,
                                     n_long=30, n_short=30)
    results["Market Neutral"] = perf
    
    return results
