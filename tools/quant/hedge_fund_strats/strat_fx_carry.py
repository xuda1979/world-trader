"""Strategy: Alternative Risk Premia — FX Carry

Classic carry: currencies with higher yields tend to appreciate vs lower-
yield currencies (the UIP deviation premium). Long top-K by yield
differential, short bottom-K, monthly rebalance.

Data (free):
  - 8 FX pairs, 2019-2026 (tools/quant/data/fx)
  - Country long-term yields, monthly (FRED OECD IRLTLT01*): us/au/jp/gb/
    ch/ca/nz/ez

Construction:
  - carry(pair CUR1_CUR2) = yield(CUR1) - yield(CUR2), long = long CUR1
  - monthly rebalance: long top-3, short bottom-3, equal weight, net 0
  - vol-scaled positions (60d), 6 bps round-trip on weight deltas, T+1
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd

try:
    from .core import BacktestEngine, compute_performance, Performance, TRADING_COST_BPS
except ImportError:  # run as script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from core import BacktestEngine, compute_performance, Performance, TRADING_COST_BPS

# pair -> (yield series names for CUR1, CUR2); long = long CUR1
PAIRS = {
    "AUD_USD": ("au10y", "us10y"),
    "EUR_GBP": ("ez10y", "gb10y"),
    "EUR_USD": ("ez10y", "us10y"),
    "GBP_USD": ("gb10y", "us10y"),
    "NZD_USD": ("nz10y", "us10y"),
    "USD_CAD": ("us10y", "ca10y"),
    "USD_CHF": ("us10y", "ch10y"),
    "USD_JPY": ("us10y", "jp10y"),
}


def load_fx(dir_path: Path = None) -> pd.DataFrame:
    if dir_path is None:
        # tools/quant/hedge_fund_strats/ -> tools/quant/data/fx
        dir_path = Path(__file__).resolve().parent.parent / "data" / "fx"
    prices = {}
    for sym in PAIRS:
        p = dir_path / f"{sym}.csv"
        if p.exists():
            df = pd.read_csv(p, parse_dates=["date"], index_col="date")
            prices[sym] = df["close"]
    return pd.DataFrame(prices)


def load_yields(dir_path: Path = None) -> pd.DataFrame:
    if dir_path is None:
        dir_path = Path(__file__).resolve().parent / "data_fred"
    out = {}
    for name in ("us10y", "au10y", "jp10y", "gb10y", "ch10y", "ca10y", "nz10y", "ez10y"):
        p = dir_path / f"{name}.csv"
        if p.exists():
            df = pd.read_csv(p, parse_dates=["date"], index_col="date")
            out[name] = df["value"]
    return pd.DataFrame(out)


def run_fx_carry(n_long: int = 3,
                 n_short: int = 3,
                 rebalance_freq: int = 21,
                 cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    print("\n" + "=" * 70)
    print("ALTERNATIVE RISK PREMIA: FX CARRY")
    print("=" * 70)
    prices = load_fx()
    yields = load_yields()
    print(f"  FX pairs: {list(prices.columns)}")
    print(f"  Yields: {list(yields.columns)}")

    # Carry per pair: yield diff (ffill monthly to daily)
    carry = pd.DataFrame(index=prices.index)
    for pair, (y1, y2) in PAIRS.items():
        if y1 in yields.columns and y2 in yields.columns:
            carry[pair] = (yields[y1] - yields[y2]).reindex(prices.index).ffill()
    # Keep full alignment with prices.index (dropna() would shift positions)
    carry = carry.ffill()
    print(f"  Carry panel: {carry.shape[0]}d x {carry.shape[1]}")

    # Vol for scaling (60d); min_periods so a single late-starting pair does
    # not poison every window (pairs start on different dates)
    returns = prices.pct_change()
    vol = returns.rolling(60, min_periods=30).std() * np.sqrt(252)

    def vol_scaled(p: str, v: pd.Series) -> float:
        """1/vol with NaN -> 0.05 fallback (max() with NaN returns NaN!)."""
        val = v.get(p, 0.05)
        if not np.isfinite(val) or val <= 0:
            val = 0.05
        return 1.0 / max(val, 0.02)

    # Weights: monthly rebalance, rank by carry, long top-n / short bottom-n.
    # Init with NaN (not 0.0) so ffill propagates targets between rebalances.
    weights = pd.DataFrame(np.nan, index=prices.index, columns=prices.columns)
    for i in range(len(carry)):
        if i % rebalance_freq != 0:
            continue
        c = carry.iloc[i].dropna()
        if len(c) < n_long + n_short:
            continue
        ranked = c.sort_values()
        shorts = ranked.index[:n_short]
        longs = ranked.index[-n_long:]
        v = vol.iloc[i]
        wvals = {}
        for p in longs:
            wvals[p] = vol_scaled(p, v)
        for p in shorts:
            wvals[p] = -vol_scaled(p, v)
        row = pd.Series(0.0, index=weights.columns)
        for p, val in wvals.items():
            row[p] = val
        g = row.abs().sum()
        if g > 0:
            weights.iloc[i] = row / g * 2.0
    # Fill targets forward: the engine's first rebalance fires at row 1
    # (last_rebal=-999), then every rebalance_freq — a phase-offset from our
    # 0,21,42... grid. Sparse rows would be invisible to it.
    weights = weights.ffill()

    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(weights, rebalance_freq=rebalance_freq)

    # Accrue the carry itself: the interest differential (rate diff in %,
    # /100 to a fraction, /252 to daily) is the economic core of a carry
    # trade — spot-only P&L misses it (spot deviations are the risk, the
    # differential is the return).
    carry_daily = (weights.shift(1) * carry / 100 / 252).sum(axis=1)
    # engine drops the first row; align carry to the engine's index
    daily_ret = daily_ret.fillna(0.0) + carry_daily.reindex(daily_ret.index).fillna(0.0)
    equity = (1 + daily_ret).cumprod()

    perf = compute_performance(daily_ret, equity, benchmark_returns=returns.mean(axis=1),
                               n_trades=int(turnover / 2), turnover_total=turnover)
    print(perf.summary())
    return perf, weights


if __name__ == "__main__":
    perf, w = run_fx_carry()
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    perf.equity_curve.to_csv(out / "equity_FX_Carry.csv")
    print("  Saved equity curve")
