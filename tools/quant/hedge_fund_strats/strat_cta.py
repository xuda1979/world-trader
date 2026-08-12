"""Strategy 5: Managed Futures / CTA (Commodity Trading Advisor)

Systematic trend following across futures markets.
Representative: AQR, Winton, Man AHL.

Signal: Multi-timeframe trend following
  - Short-term: 20-day breakout
  - Medium-term: 50-day momentum
  - Long-term: 200-day trend
  - Combined with volatility scaling

Key features:
  - Long and short (can profit in bear markets)
  - Volatility target (e.g., 15% annualized)
  - Dynamic position sizing based on signal strength
  - Diversified across many instruments

Since we have equity + FX + crypto data, we apply CTA methodology
to all available instruments as a cross-asset trend follower.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from .core import DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS


def compute_breakout_signal(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Donchian channel breakout signal.
    
    +1 if price > max(high of last N days)
    -1 if price < min(low of last N days)
    0 otherwise (inside channel)
    """
    rolling_max = prices.rolling(lookback).max().shift(1)
    rolling_min = prices.rolling(lookback).min().shift(1)
    
    signal = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    signal[prices > rolling_max] = 1.0
    signal[prices < rolling_min] = -1.0
    
    return signal


def compute_trend_strength(prices: pd.DataFrame, fast: int = 10, slow: int = 50) -> pd.DataFrame:
    """ADXR-style trend strength: |fast MA - slow MA| / slow MA.
    
    Values near 0 = no trend, large values = strong trend.
    """
    fast_ma = prices.rolling(fast).mean()
    slow_ma = prices.rolling(slow).mean()
    strength = (fast_ma - slow_ma) / slow_ma
    return strength


def compute_multi_timeframe_signal(prices: pd.DataFrame) -> pd.DataFrame:
    """Combine signals across multiple timeframes.
    
    Short (20-day), Medium (50-day), Long (200-day) trends.
    Weight: 0.5 short + 0.3 medium + 0.2 long
    """
    # Short-term: 20-day breakout
    short_sig = compute_breakout_signal(prices, lookback=20)
    
    # Medium-term: 50-day momentum direction
    med_ret = prices.shift(5) / prices.shift(50) - 1
    med_sig = np.sign(med_ret)
    
    # Long-term: 200-day trend
    long_ret = prices.shift(21) / prices.shift(200) - 1
    long_sig = np.sign(long_ret)
    
    # Combined signal
    combined = 0.5 * short_sig + 0.3 * med_sig + 0.2 * long_sig
    
    # Normalize to [-1, 1]
    combined = combined.clip(-1, 1)
    
    return combined


def vol_target_weights(signal: pd.DataFrame, returns: pd.DataFrame,
                       target_vol: float = 0.15,
                       lookback: int = 60) -> pd.DataFrame:
    """Scale positions to achieve target portfolio volatility.
    
    weight_i = signal_i / vol_i * scale
    where scale targets total portfolio vol = target_vol
    """
    # Per-asset volatility
    vol = returns.rolling(lookback).std() * np.sqrt(252)
    vol = vol.replace(0, np.nan).ffill()
    
    # Inverse vol weighted signal
    inv_vol_signal = signal / vol
    
    # Portfolio vol estimate
    port_ret = (inv_vol_signal.shift(1) * returns).sum(axis=1)
    port_vol = port_ret.rolling(lookback).std() * np.sqrt(252)

    # Scale factor
    scale = target_vol / port_vol.replace(0, np.nan)
    scale = scale.clip(0, 2.0).ffill()  # cap leverage multiplier at 2x

    # Final weights (inverse-vol * trend signal * vol-target scale)
    weights = inv_vol_signal.mul(scale, axis=0)

    # Cap individual position at 20% of capital
    weights = weights.clip(-0.20, 0.20)

    # Cap total gross leverage at 1.5x (retail constraint)
    for i in range(len(weights)):
        row = weights.iloc[i]
        gross = row.abs().sum()
        if gross > 1.5:
            weights.iloc[i] = (row / gross * 1.5).values

    return weights


def run_cta(prices: pd.DataFrame,
            returns: pd.DataFrame,
            fx_prices: Optional[pd.DataFrame] = None,
            crypto_prices: Optional[pd.DataFrame] = None,
            target_vol: float = 0.15,
            rebalance_freq: int = 5,
            cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    """Run Managed Futures / CTA strategy backtest.
    
    Args:
        prices: equity/ETF prices
        returns: equity/ETF returns
        fx_prices: FX pair prices (optional)
        crypto_prices: crypto prices (optional)
        target_vol: target annualized portfolio volatility
        rebalance_freq: rebalance every N days
        cost_bps: round-trip cost
    """
    print("\n" + "="*70)
    print("STRATEGY 5: MANAGED FUTURES / CTA (Trend Following)")
    print("="*70)
    
    # Combine all available assets
    all_prices = prices.copy()
    all_returns = returns.copy()
    
    if fx_prices is not None and len(fx_prices) > 100:
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
    print(f"  Target vol: {target_vol:.0%}")
    print(f"  Rebalance: every {rebalance_freq} days")
    print(f"  Cost: {cost_bps} bps round-trip")
    
    # Compute multi-timeframe trend signals
    print("  Computing multi-timeframe trend signals...")
    signal = compute_multi_timeframe_signal(all_prices)
    
    # Volatility target
    print("  Applying volatility targeting...")
    weights = vol_target_weights(signal, all_returns, target_vol=target_vol)
    
    # Run backtest
    engine = BacktestEngine(all_prices.dropna(how='all'), cost_bps=cost_bps)
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


def run_cta_variants(prices: pd.DataFrame, returns: pd.DataFrame,
                     fx_prices: pd.DataFrame = None,
                     crypto_prices: pd.DataFrame = None) -> Dict[str, Performance]:
    """Run CTA with different parameter sets."""
    results = {}

    # Monthly rebalance, 15% vol target (standard multi-timeframe CTA)
    perf, _ = run_cta(prices, returns, fx_prices, crypto_prices,
                      target_vol=0.15, rebalance_freq=21)
    results["CTA_15vol_21d"] = perf

    # Monthly rebalance, 10% vol target (lower risk)
    perf, _ = run_cta(prices, returns, fx_prices, crypto_prices,
                      target_vol=0.10, rebalance_freq=21)
    results["CTA_10vol_21d"] = perf

    # Short-term breakout, monthly rebalance (higher turnover, still 21d)
    perf, _ = run_cta(prices, returns, fx_prices, crypto_prices,
                      target_vol=0.15, rebalance_freq=10)
    results["CTA_15vol_10d"] = perf

    return results
