"""Strategy 3: Global Macro

Top-down allocation across asset classes: equities, FX, bonds, commodities.
Representative funds: Soros Quantum Fund, Bridgewater (Dalio).

Signal: Multi-asset trend following + carry + macro regime
  - Equity index: SPY/QQQ trend (200-day MA crossover)
  - FX: currency momentum and carry
  - Bonds: duration timing via TLT proxy
  - Commodities: GLD trend
  - Risk-on/off regime switching

Since we have limited macro instruments, we use:
  - SPY/QQQ (equity index)
  - GLD (gold proxy, if available)
  - FX pairs (EUR/USD, GBP/USD, USD/JPY, etc.)
  - BTC/ETH (digital assets)
  - Sector ETFs (XLF, etc.)
  - VIX proxy from realized volatility
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from .core import DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS


def compute_trend_signal(prices: pd.DataFrame, fast: int = 20, slow: int = 200) -> pd.DataFrame:
    """Compute trend-following signals using MA crossover.
    
    Signal = +1 if fast MA > slow MA, -1 otherwise.
    Strength = (fast MA - slow MA) / slow MA
    """
    fast_ma = prices.rolling(fast).mean()
    slow_ma = prices.rolling(slow).mean()
    
    # Direction: +1 or -1
    direction = np.sign(fast_ma - slow_ma)
    
    # Strength: normalized by slow MA
    strength = (fast_ma - slow_ma) / slow_ma
    
    return direction * strength.clip(-1, 1)


def compute_momentum_signal(prices: pd.DataFrame, lookback: int = 120,
                             skip: int = 21) -> pd.DataFrame:
    """Compute momentum signal: past return skipping recent month."""
    return prices.shift(skip) / prices.shift(lookback + skip) - 1


def compute_carry_signal_fx(fx_prices: pd.DataFrame) -> pd.DataFrame:
    """For FX, carry signal = recent drift (proxy for interest rate differential).
    
    In real implementation, this would use actual rate differentials.
    Here we use 60-day drift as a proxy.
    """
    returns = fx_prices.pct_change()
    carry = returns.rolling(60).mean() * 252  # annualized drift
    return carry


def compute_vol_regime(returns: pd.DataFrame, window: int = 60,
                       threshold: float = 1.5) -> pd.Series:
    """Compute volatility regime indicator.
    
    Returns a series: 1 = normal, 0.5 = elevated vol, 0 = crisis
    """
    # Average cross-sectional volatility
    avg_vol = returns.mean(axis=1).rolling(window).std() * np.sqrt(252)
    avg_vol = avg_vol.fillna(0.15)
    
    # Long-term average vol
    long_vol = avg_vol.rolling(252).mean().fillna(0.15)
    
    regime = pd.Series(1.0, index=returns.index)
    regime[avg_vol > long_vol * threshold] = 0.5  # elevated
    regime[avg_vol > long_vol * 2.0] = 0.0  # crisis
    
    return regime


def run_global_macro(equity_prices: pd.DataFrame,
                     equity_returns: pd.DataFrame,
                     fx_prices: Optional[pd.DataFrame] = None,
                     crypto_prices: Optional[pd.DataFrame] = None,
                     cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    """Run Global Macro strategy backtest.
    
    Allocates across asset classes based on:
      - Trend following (MA crossover)
      - Momentum (120-day return skip 1 month)
      - Vol regime scaling (reduce risk in crisis)
    
    Args:
        equity_prices: stock/ETF prices
        equity_returns: stock/ETF returns
        fx_prices: FX pair prices (optional)
        crypto_prices: crypto prices (optional)
        cost_bps: round-trip cost
    """
    print("\n" + "="*70)
    print("STRATEGY 3: GLOBAL MACRO")
    print("="*70)
    
    # Combine all available assets
    all_prices = equity_prices.copy()
    all_returns = equity_returns.copy()
    
    if fx_prices is not None and len(fx_prices) > 100:
        # Align FX to equity dates
        fx_aligned = fx_prices.reindex(all_prices.index).ffill()
        all_prices = all_prices.join(fx_aligned.add_suffix('_FX'), how='left')
        fx_returns = fx_aligned.pct_change().add_suffix('_FX')
        all_returns = all_returns.join(fx_returns, how='left')
        print(f"  FX assets: {fx_prices.shape[1]}")
    
    if crypto_prices is not None and len(crypto_prices) > 100:
        crypto_aligned = crypto_prices.reindex(all_prices.index).ffill()
        all_prices = all_prices.join(crypto_aligned.add_suffix('_CRYPTO'), how='left')
        crypto_returns = crypto_aligned.pct_change().add_suffix('_CRYPTO')
        all_returns = all_returns.join(crypto_returns, how='left')
        print(f"  Crypto assets: {crypto_prices.shape[1]}")
    
    print(f"  Total assets: {all_prices.shape[1]}")
    print(f"  Date range: {all_prices.index[0].date()} to {all_prices.index[-1].date()}")
    print(f"  Cost: {cost_bps} bps round-trip")
    
    # Compute signals
    print("  Computing trend + momentum signals...")
    trend = compute_trend_signal(all_prices, fast=20, slow=200)
    momentum = compute_momentum_signal(all_prices, lookback=120, skip=21)
    
    # Combine: 60% trend, 40% momentum
    combined = 0.6 * np.sign(trend) * trend.abs().clip(0, 1) + \
               0.4 * momentum.rank(axis=1, pct=True).sub(0.5).mul(2)
    
    # Vol regime scaling
    print("  Computing volatility regime...")
    regime = compute_vol_regime(all_returns, window=60)
    
    # Scale positions by regime
    weights = combined.mul(regime, axis=0)
    
    # Normalize: equal weight across active positions
    for i in range(len(weights)):
        row = weights.iloc[i].dropna()
        active = row[row != 0]
        if len(active) > 0:
            # Cap individual position at 20% of portfolio
            n_assets = len(active)
            target_weight = min(1.0 / n_assets * 2, 0.20)
            date = weights.index[i]
            new_row = pd.Series(0.0, index=weights.columns)
            new_row[active.index] = np.sign(active) * target_weight
            # Scale to total gross = 1.0
            gross = new_row.abs().sum()
            if gross > 0:
                new_row = new_row / gross
            weights.iloc[i] = new_row.values
    
    # Run backtest
    # Use only the equity portion for the engine (since other assets are joined)
    engine = BacktestEngine(all_prices.dropna(how='all'), cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=21)
    
    # Benchmark
    spy_col = "SPY" if "SPY" in equity_returns.columns else None
    bench = equity_returns[spy_col] if spy_col else equity_returns.mean(axis=1)
    
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=int(turnover / 2),
                               turnover_total=turnover)
    
    print(f"\n  Results:")
    print(perf.summary())
    
    return perf, weights


def run_bridgewater_style(prices: pd.DataFrame, returns: pd.DataFrame,
                          cost_bps: float = TRADING_COST_BPS) -> Performance:
    """Bridgewater All-Weather style risk parity.
    
    Allocates risk equally across asset classes, not capital.
    Lower vol assets get more capital, higher vol less.
    """
    print("\n  --- Bridgewater All-Weather Style (Risk Parity) ---")
    
    # Compute rolling volatility
    vol = returns.rolling(60).std() * np.sqrt(252)
    vol = vol.replace(0, np.nan).ffill()
    
    # Inverse volatility weights
    inv_vol = 1 / vol
    weights = inv_vol.div(inv_vol.sum(axis=1), axis=0)
    
    # Scale to target 10% annual vol
    port_vol = (weights * returns).sum(axis=1).rolling(60).std() * np.sqrt(252)
    scale = 0.10 / port_vol.replace(0, np.nan)
    scale = scale.clip(0, 3).ffill()
    weights = weights.mul(scale, axis=0)
    
    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=21)
    
    spy_col = "SPY" if "SPY" in returns.columns else None
    bench = returns[spy_col] if spy_col else returns.mean(axis=1)
    
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=int(turnover / 2),
                               turnover_total=turnover)
    print(perf.summary())
    return perf
