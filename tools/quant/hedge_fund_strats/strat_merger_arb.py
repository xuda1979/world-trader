"""Strategy 4: Merger Arbitrage (Event-Driven)

Profit from spread between acquisition offer price and target's current price.
After deal announcement: long target, short acquirer.

Since we don't have real merger announcement data, we implement a 
*proxy* strategy that captures the same risk profile:
  1. Earnings event drift: post-earnings announcement drift (PEAD)
  2. Sudden price jump detection: identify stocks that jumped >5% in a day
     (proxy for event-driven moves) and trade the continuation/reversal
  3. Pair trade: when stock A jumps relative to stock B (same sector),
     short A / long B expecting convergence

This gives similar return profile to merger arb: 
  - Many small wins, occasional large loss (deal break proxy)
  - Low market beta
  - Event-dependent
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
from .core import DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS


def detect_event_jumps(returns: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """Detect abnormal price jumps (proxy for corporate events).
    
    Returns binary DataFrame: 1 = event detected, 0 = no event.
    """
    # Jump = daily return exceeds threshold
    jumps = (returns.abs() > threshold).astype(float)
    
    # Only count positive jumps for long (acquisition target proxy)
    pos_jumps = (returns > threshold).astype(float)
    neg_jumps = (returns < -threshold).astype(float)
    
    return pos_jumps, neg_jumps


def compute_pead_signals(returns: pd.DataFrame, prices: pd.DataFrame,
                         event_window: int = 3,
                         holding_period: int = 20,
                         threshold: float = 0.03,
                         max_concurrent: int = 10) -> pd.DataFrame:
    """Post-Earnings Announcement Drift (PEAD) proxy.

    When a stock has an abnormal return > threshold over `event_window` days:
      - Positive surprise: go long (drift continues)
      - Negative surprise: go short (drift continues)

    Hold for `holding_period` days then exit. To keep each position
    economically meaningful (and avoid turnover costs overwhelming tiny
    positions), we cap the number of CONCURRENT active positions to
    `max_concurrent` and equal-weight them.
    """
    # 3-day cumulative return
    cum_3d = (1 + returns).rolling(event_window).apply(np.prod, raw=True) - 1

    # Target-weight signal: 0 = flat. Each day we hold up to max_concurrent
    # open bets (longs and shorts combined), each sized 1/max_concurrent.
    signals = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)

    # Track open positions and their remaining days
    open_pos = {}  # (date_enter, ticker, side) -> remaining days
    target = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)

    # Simpler robust approach: build the weight book once by iterating days.
    for i in range(event_window, len(returns)):
        date = prices.index[i]
        cum = cum_3d.iloc[i]

        # Find NEW events today (only those not already held)
        pos_events = cum[cum > threshold]
        neg_events = cum[cum < -threshold]

        # Combine new + existing open, capped
        # Existing positions stay until holding_period expires
        # Simple approach: compute signal as equal-weight across whatever is
        # currently "active" (opened in the last holding_period window),
        # capped to the strongest `max_concurrent` by |event magnitude|.
        active = []
        for d in range(max(0, i - holding_period), i):
            c = cum_3d.iloc[d]
            # events that fired at day d
            for t in c[c.abs() > threshold].index:
                active.append((d, t, np.sign(c[t]), abs(c[t])))

        # Dedupe: keep most recent signal per ticker
        seen = {}
        for d, t, side, mag in active:
            seen[t] = (side, d, mag)
        # Cap to strongest max_concurrent
        ranked = sorted(seen.items(), key=lambda kv: -kv[1][2])[:max_concurrent]

        if ranked:
            w = 1.0 / len(ranked)
            for t, (side, d, mag) in ranked:
                # Count as a position only if within its holding window
                if i - d <= holding_period:
                    signals.loc[date, t] = w * side

    return signals


def compute_pair_convergence(returns: pd.DataFrame, prices: pd.DataFrame,
                             window: int = 60,
                             z_threshold: float = 2.0,
                             holding_period: int = 15) -> pd.DataFrame:
    """Sector pair convergence: when one stock outperforms its sector, 
    expect convergence (reversal).
    
    For each stock, compute its relative return vs sector average.
    If relative return > z_threshold standard deviations, short it.
    If < -z_threshold, long it.
    """
    # Sector average return (equal-weight cross section)
    sector_avg = returns.mean(axis=1)
    
    # Relative return
    rel_ret = returns.sub(sector_avg, axis=0)
    
    # Rolling z-score of relative return
    rel_mean = rel_ret.rolling(window).mean()
    rel_std = rel_ret.rolling(window).std()
    z_score = (rel_ret - rel_mean) / rel_std.replace(0, np.nan)
    
    # Signals
    signals = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    
    for i in range(window, len(z_score)):
        z = z_score.iloc[i]
        date = signals.index[i]

        # Short stocks that outperformed sector significantly
        shorts = z[z > z_threshold]
        if len(shorts) > 0:
            signals.loc[date, shorts.index] = -1.0 / len(shorts)

        # Long stocks that underperformed
        longs = z[z < -z_threshold]
        if len(longs) > 0:
            signals.loc[date, longs.index] = 1.0 / len(longs)
    
    return signals


def run_merger_arb_proxy(prices: pd.DataFrame,
                         returns: pd.DataFrame,
                         method: str = "pead",
                         threshold: float = 0.03,
                         holding_period: int = 20,
                         cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    """Run Merger Arbitrage proxy backtest.
    
    Args:
        method: 'pead' (post-earnings drift) or 'pair' (sector convergence)
        threshold: event detection threshold
        holding_period: days to hold position
        cost_bps: round-trip cost
    """
    print("\n" + "="*70)
    print("STRATEGY 4: MERGER ARBITRAGE (Event-Driven Proxy)")
    print("="*70)
    print(f"  Method: {method}")
    print(f"  Event threshold: {threshold:.1%}")
    print(f"  Holding period: {holding_period} days")
    print(f"  Cost: {cost_bps} bps round-trip")
    
    if method == "pead":
        print("  Computing PEAD (Post-Earnings Announcement Drift) signals...")
        signals = compute_pead_signals(returns, prices,
                                        event_window=3,
                                        holding_period=holding_period,
                                        threshold=threshold)
    elif method == "pair":
        print("  Computing sector pair convergence signals...")
        signals = compute_pair_convergence(returns, prices,
                                            window=60,
                                            z_threshold=2.0,
                                            holding_period=holding_period)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # Count events
    n_events = (signals != 0).sum().sum()
    print(f"  Total event positions: {n_events}")
    
    # Scale signals to target gross leverage of 1.0
    for i in range(len(signals)):
        row = signals.iloc[i]
        gross = row.abs().sum()
        if gross > 1.0:
            signals.iloc[i] = (row / gross).values
    
    # Run backtest
    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover, n_trades = engine.run_signal_based(
        signals, holding_period=holding_period)
    
    # Benchmark
    spy_col = "SPY" if "SPY" in returns.columns else None
    bench = returns[spy_col] if spy_col else returns.mean(axis=1)
    
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=n_trades,
                               turnover_total=turnover)
    
    print(f"\n  Results:")
    print(perf.summary())
    
    return perf, signals


def run_merger_arb_combined(prices: pd.DataFrame,
                            returns: pd.DataFrame,
                            cost_bps: float = TRADING_COST_BPS) -> Dict[str, Performance]:
    """Run multiple merger arb proxy variants."""
    results = {}
    
    # PEAD with different thresholds
    for thresh, label in [(0.02, "PEAD_2pct"), (0.03, "PEAD_3pct"), (0.05, "PEAD_5pct")]:
        perf, _ = run_merger_arb_proxy(prices, returns, method="pead",
                                        threshold=thresh, holding_period=20,
                                        cost_bps=cost_bps)
        results[label] = perf
    
    # Sector pair convergence
    perf, _ = run_merger_arb_proxy(prices, returns, method="pair",
                                    holding_period=15, cost_bps=cost_bps)
    results["Sector_Pair"] = perf
    
    return results
