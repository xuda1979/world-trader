"""Managed Futures / CTA on REAL futures (Stooq data, free).

The taxonomy's CTA definition: systematic trading of commodity futures,
financial futures and options. The base CTA in this suite trades
equities/FX/crypto; this variant trades an actual futures universe:
  - Equity index: ES (S&P500), NQ (Nasdaq), YM (Dow)
  - Energy: CL (crude), NG (nat gas), RB (gasoline), HO (heat)
  - Metals: GC (gold), SI (silver), HG (copper)
  - Rates: ZB (30y), ZN (10y), ZF (5y)
  - FX: 6E (EUR), 6J (JPY), 6B (GBP), 6C (CAD), 6A (AUD)
  - Ags: ZC (corn), ZS (soybeans), ZW (wheat)

Signal: classic multi-timeframe trend following (AQR/Winton style):
  0.5*20d breakout + 0.3*50d momentum + 0.2*200d trend, inverse-vol
  weighted, 15% vol target, per-instrument cap 20%, gross cap 1.5x.

6 bps round-trip cost on weight deltas, T+1 execution.
"""

import sys
import os
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
try:
    from .core import BacktestEngine, compute_performance, Performance, TRADING_COST_BPS
except ImportError:  # run as script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from core import BacktestEngine, compute_performance, Performance, TRADING_COST_BPS

FUTURES = [
    "es", "nq", "ym", "cl", "ng", "rb", "ho",
    "gc", "si", "hg", "zb", "zn", "zf",
    "6e", "6j", "6b", "6c", "6a", "zc", "zs", "zw",
]

# FRED daily series (free, unlimited): commodities, rates, FX, equity indices.
# gold missing — LBMA AM/PM fixes discontinued on FRED. OPT-IN metals now
# available in data_fred/ (xau.csv, slv.csv, copx.csv — twelvedata free tier,
# converted 2026-08-13): append "xau", "slv", "copx" to test a 17-inst leg.
# NOT adopted by default: flagship daily MaxDD worsens -12.9% -> -15.0%
# (monthly aggregates flat; see RESEARCH_LOG 2026-08-13 metals entry).
FRED = [
    "wti", "brent", "natgas", "us2y", "us10y", "us30y",
    "eur", "jpy", "gbp", "cad", "cny", "spx", "dow", "vix",
]


def load_futures(dir_path: Path = None) -> Dict[str, pd.DataFrame]:
    """Stooq futures (Date,Open,High,Low,Close,Volume) or FRED (date,value)."""
    if dir_path is None:
        dir_path = Path(__file__).resolve().parent / "data_stooq"
    data = {}
    for sym in FUTURES:
        p = dir_path / f"{sym}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p, parse_dates=["Date"], index_col="Date")
        df = df[["Close"]].rename(columns={"Close": "close"}).sort_index()
        data[sym] = df
    if not data:
        print("  no Stooq futures found; trying FRED series...")
        fred_dir = dir_path.parent / "data_fred"
        for sym in FRED:
            p = fred_dir / f"{sym}.csv"
            if not p.exists():
                continue
            df = pd.read_csv(p, parse_dates=["date"], index_col="date")
            # Guard: reject sparse files (e.g. a monthly series accidentally
            # written over a daily one) — ffill would mask them.
            if len(df) < 500:
                print(f"  (skipping {sym}: only {len(df)} rows — too sparse)")
                continue
            df.columns = ["close"]
            data[sym] = df
    return data


def compute_multi_timeframe_signal(prices: pd.DataFrame) -> pd.DataFrame:
    """0.5*20d breakout + 0.3*50d momentum + 0.2*200d trend, clipped to [-1,1]."""
    roll_max = prices.rolling(20).max().shift(1)
    roll_min = prices.rolling(20).min().shift(1)
    short_sig = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    short_sig[prices > roll_max] = 1.0
    short_sig[prices < roll_min] = -1.0

    med_ret = prices.shift(5) / prices.shift(50) - 1
    med_sig = np.sign(med_ret)

    long_ret = prices.shift(21) / prices.shift(200) - 1
    long_sig = np.sign(long_ret)

    combined = 0.5 * short_sig + 0.3 * med_sig + 0.2 * long_sig
    return combined.clip(-1, 1)


def vol_target_weights(signal: pd.DataFrame, returns: pd.DataFrame,
                       target_vol: float = 0.15, lookback: int = 60) -> pd.DataFrame:
    vol = returns.rolling(lookback).std() * np.sqrt(252)
    vol = vol.replace(0, np.nan).ffill()
    inv_vol_signal = signal / vol
    port_ret = (inv_vol_signal.shift(1) * returns).sum(axis=1)
    port_vol = port_ret.rolling(lookback).std() * np.sqrt(252)
    scale = (target_vol / port_vol.replace(0, np.nan)).clip(0, 2.0).ffill()
    weights = inv_vol_signal.mul(scale, axis=0)
    weights = weights.clip(-0.20, 0.20)
    for i in range(len(weights)):
        row = weights.iloc[i]
        gross = row.abs().sum()
        if gross > 1.5:
            weights.iloc[i] = row / gross * 1.5
    return weights


def run_cta_futures(target_vol: float = 0.15,
                    rebalance_freq: int = 5,
                    cost_bps: float = TRADING_COST_BPS,
                    min_history: int = 300,
                    signal_mode: str = "multi") -> Tuple[Performance, pd.DataFrame]:
    """Run Managed Futures / CTA on the real futures universe.

    signal_mode: 'multi' = 0.5*20d breakout + 0.3*50d + 0.2*200d trend
                 'tsmom' = sign of 50d/200d return (classic time-series momentum)
    """
    print("\n" + "=" * 70)
    print("CTA ON REAL FUTURES / MACRO (Stooq/FRED)")
    print("=" * 70)
    data = load_futures()
    print(f"  Loaded {len(data)} futures instruments")

    # Build panel (start after all major instruments exist)
    prices = pd.DataFrame({sym: df["close"] for sym, df in data.items()})
    prices = prices.dropna(how='all').ffill(limit=5)
    prices = prices[prices.index >= "2008-01-01"]
    # Only instruments with enough history
    ok = [c for c in prices.columns if prices[c].count() > min_history]
    prices = prices[ok]
    # Invert yields: a rates CTA trades the BOND direction (long bond = short yield)
    for y in ("us2y", "us10y", "us30y"):
        if y in prices.columns:
            prices[y] = -prices[y]
    returns = prices.pct_change()
    print(f"  Panel: {prices.shape[0]}d x {prices.shape[1]} instruments")
    print(f"  Range: {prices.index[0].date()} to {prices.index[-1].date()}")

    if signal_mode == "tsmom":
        signal = np.sign(prices.shift(50) / prices.shift(200) - 1)
    else:
        signal = compute_multi_timeframe_signal(prices)
    weights = vol_target_weights(signal, returns, target_vol=target_vol)

    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=rebalance_freq)

    bench = returns.mean(axis=1)  # EW futures index
    perf = compute_performance(daily_ret, equity, benchmark_returns=bench,
                               n_trades=int(turnover / 2),
                               turnover_total=turnover)
    print(perf.summary())
    return perf, weights


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    for mode, tag in [("multi", "multi"), ("tsmom", "tsmom")]:
        for reb, rtag in [(10, "10d"), (21, "21d")]:
            perf, _ = run_cta_futures(rebalance_freq=reb, signal_mode=mode)
            perf.equity_curve.to_csv(out / f"equity_CTA_Futures_{tag}_{rtag}.csv")
    print("  Saved equity curves")
