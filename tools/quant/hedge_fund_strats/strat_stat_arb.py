"""Strategy: Relative Value / Statistical Arbitrage (pairs trading)

Classic market-neutral pairs strategy on the equity universe:
  - Every refit window (default 126 trading days), select the top-N pairs
    by 60-day return correlation among liquid names with full history.
  - For each selected pair, compute the log-price spread and its z-score
    over the refit window.
  - Entry: |z| > entry_z  -> long the lagging (underpriced) leg, short the
    leading (overpriced) leg, equal $ per pair.
  - Exit:  |z| < exit_z   -> flat.
  - Equal dollar allocation across active pairs; gross capped at 2.0x.

This is the pure alpha branch of the Relative Value category: no market
beta by construction (every pair is dollar neutral), profits from
convergence of pricing deviations between related securities.

T+1 execution via BacktestEngine; 6 bps round-trip cost on weight deltas.
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Optional
from .core import DataLoader, BacktestEngine, compute_performance, Performance, TRADING_COST_BPS


def select_pairs(returns: pd.DataFrame, n_pairs: int = 40,
                 corr_window: int = 60, min_price: float = 2.0) -> List[Tuple[str, str]]:
    """Select top-N pairs by rolling return correlation (end of sample window)."""
    # Use the last corr_window days of the given window
    recent = returns.tail(corr_window)
    corr = recent.corr().values
    tickers = returns.columns.tolist()
    n = len(tickers)

    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            c = corr[i, j]
            if np.isnan(c):
                continue
            pairs.append((tickers[i], tickers[j], c))
    pairs.sort(key=lambda x: -x[2])
    return [(a, b) for a, b, _ in pairs[:n_pairs]]


def compute_pair_weights(prices: pd.DataFrame,
                         pairs: List[Tuple[str, str]],
                         entry_z: float = 1.5,
                         exit_z: float = 0.5,
                         z_window: int = 60,
                         max_gross: float = 2.0) -> pd.DataFrame:
    """Compute target weights for the given pair basket.

    Returns DataFrame[T, N] of portfolio weights:
      +0.5/gross_normalized for long legs, -0.5/... for short legs.
    """
    weights = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)

    # Log-price panel for spread computation
    logp = np.log(prices)

    for a, b in pairs:
        if a not in logp.columns or b not in logp.columns:
            continue
        spread = logp[a] - logp[b]
        mu = spread.rolling(z_window).mean()
        sd = spread.rolling(z_window).std()
        z = (spread - mu) / sd.replace(0, np.nan)
        z = z.ffill()

        # Signal: entry when |z| > entry_z, exit when |z| < exit_z (hysteresis)
        sig_long = (z > entry_z).astype(float)   # b lagging -> long b, short a
        sig_short = (z < -entry_z).astype(float)  # a lagging -> long a, short b
        # Exit once position entered and z crosses back below exit_z
        # (state machine via running exit condition on consecutive pairs)
        state = np.zeros(len(z))
        for i in range(1, len(z)):
            zi = z.iloc[i]
            if state[i - 1] == 0:
                if zi > entry_z:
                    state[i] = 1
                elif zi < -entry_z:
                    state[i] = -1
            else:
                if abs(zi) < exit_z:
                    state[i] = 0
                else:
                    state[i] = state[i - 1]
        # state = +1: long b, short a ; -1: long a, short b
        sgn = np.sign(state)
        weights.loc[:, b] += np.where(state != 0, sgn, 0.0)
        weights.loc[:, a] -= np.where(state != 0, sgn, 0.0)

    # Cap book gross at max_gross. NOTE: this is LEVERAGE control, not a pair
    # count limit — 30-40 pairs are typically active simultaneously; gross
    # without the cap would be ~70-80x. (Diagnosed via sweep: removing the cap
    # -> 219% annualized vol -> -100% return.)
    for i in range(len(weights)):
        row = weights.iloc[i]
        gross = row.abs().sum()
        if gross > max_gross:
            weights.iloc[i] = row / gross * max_gross
    return weights


def run_stat_arb(prices: pd.DataFrame,
                 returns: pd.DataFrame,
                 n_pairs: int = 40,
                 entry_z: float = 1.5,
                 exit_z: float = 0.5,
                 refit_freq: int = 126,
                 rebalance_freq: int = 5,
                 min_history_days: int = 500,
                 cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    """Run Relative Value / statistical arbitrage backtest.

    Pairs are re-selected every `refit_freq` days from the trailing window.
    """
    print("\n" + "=" * 70)
    print("STRATEGY 6: RELATIVE VALUE / STATISTICAL ARBITRAGE (PAIRS)")
    print("=" * 70)
    print(f"  Universe: {prices.shape[1]} equities")
    print(f"  Pairs: top {n_pairs} by 60d correlation, refit every {refit_freq}d")
    print(f"  Entry |z| > {entry_z}, exit |z| < {exit_z}")
    print(f"  Rebalance: every {rebalance_freq} days")
    print(f"  Cost: {cost_bps} bps round-trip")

    # Restrict to names with enough history
    good = prices.columns[prices.count() > min_history_days]
    prices_u = prices[good]
    returns_u = returns[good]
    print(f"  Liquid names: {len(good)}")

    # Build target weights by refitting the pair basket over time.
    # At each refit point s: pairs are selected from the trailing refit_freq
    # days BEFORE s (no look-ahead into the traded segment), and z-scores are
    # computed on a panel with an extra 60-day warm-up so the state machine
    # carries real spread history into the traded segment [s, end).
    weights = pd.DataFrame(0.0, index=prices_u.index, columns=prices_u.columns)
    refit_pts = list(range(min_history_days, len(prices_u), refit_freq))
    for k, s in enumerate(refit_pts):
        end = refit_pts[k + 1] if k + 1 < len(refit_pts) else len(prices_u)
        sel_ret = returns_u.iloc[s - refit_freq:s]
        if sel_ret.shape[0] < 120:
            continue
        pairs = select_pairs(sel_ret, n_pairs=n_pairs)
        z_price = prices_u.iloc[max(0, s - refit_freq - 60):end]
        w = compute_pair_weights(z_price, pairs,
                                 entry_z=entry_z, exit_z=exit_z,
                                 z_window=60)
        seg_len = end - s
        weights.iloc[s:end] = w.iloc[len(w) - seg_len:].values

    # Run backtest
    engine = BacktestEngine(prices_u, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=rebalance_freq)

    bench = returns[["SPY"]].iloc[:, 0] if "SPY" in returns.columns else returns.mean(axis=1)
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=int(turnover / 2),
                               turnover_total=turnover)

    print(f"\n  Results:")
    print(perf.summary())
    return perf, weights


def run_stat_arb_variants(prices: pd.DataFrame,
                          returns: pd.DataFrame) -> Dict[str, Performance]:
    """Run stat arb with a few parameter sets."""
    results = {}

    perf, _ = run_stat_arb(prices, returns, n_pairs=40, entry_z=1.5, exit_z=0.5,
                           refit_freq=126, rebalance_freq=5)
    results["StatArb_40pairs_z15"] = perf

    # Tighter entry (more trades, faster mean reversion capture)
    perf, _ = run_stat_arb(prices, returns, n_pairs=40, entry_z=1.0, exit_z=0.3,
                           refit_freq=126, rebalance_freq=5)
    results["StatArb_40pairs_z10"] = perf

    # Wider pair basket
    perf, _ = run_stat_arb(prices, returns, n_pairs=80, entry_z=1.5, exit_z=0.5,
                           refit_freq=126, rebalance_freq=5)
    results["StatArb_80pairs_z15"] = perf

    return results
