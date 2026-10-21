"""Strategy: Fixed Income Arbitrage (Relative Value)

Classic curve-trade: the 10y-2y (and 30y-10y) yield spread mean-reverts.
When the curve is stretched (|z| > entry), bet on reversion:
  - z > +entry (curve steep)  -> short the spread (flattener trade)
  - z < -entry (curve flat/inverted) -> long the spread (steepener trade)
Exit when |z| < exit.

Implementation notes:
  - "Price" of each instrument is the yield SPREAD in % (10y-2y, 30y-10y).
  - We trade the spread series directly (long = +1 spread unit): a flattener
    in yield terms = short 10y bond + long 2y bond. Trades the series
    directionally; direction labels follow the spread itself.
  - Signals are yield changes (tiny); 6 bps cost is material vs daily
    spread moves — honest test of whether the curve edge survives costs.
  - Inverse-vol position sizing, gross cap 1.0, weekly rebalance, T+1.
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

SPREADS = [("us10y", "us2y", "10y2y"), ("us30y", "us10y", "30y10y")]


def load_yields(dir_path: Path = None) -> pd.DataFrame:
    if dir_path is None:
        dir_path = Path(__file__).resolve().parent / "data_fred"
    series = {}
    for name in ("us2y", "us10y", "us30y"):
        p = dir_path / f"{name}.csv"
        if p.exists():
            df = pd.read_csv(p, parse_dates=["date"], index_col="date")
            series[name] = df["value"]
    return pd.DataFrame(series)


def run_fi_arb(entry_z: float = 1.5,
               exit_z: float = 0.5,
               z_window: int = 60,
               rebalance_freq: int = 5,
               cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    print("\n" + "=" * 70)
    print("STRATEGY: FIXED INCOME ARBITRAGE (curve spread mean reversion)")
    print("=" * 70)
    yields = load_yields()
    print(f"  Yields: {list(yields.columns)}")

    spreads = pd.DataFrame(index=yields.index)
    for a, b, name in SPREADS:
        if a in yields.columns and b in yields.columns:
            spreads[name] = yields[a] - yields[b]
    spreads = spreads.dropna(how="all").ffill(limit=5)
    spreads = spreads[spreads.index >= "2008-01-01"]
    print(f"  Spreads: {spreads.shape[0]}d x {spreads.shape[1]} ({list(spreads.columns)})")

    # Position = sign-based on z with hysteresis; size = 1 (single unit spread)
    weights = pd.DataFrame(0.0, index=spreads.index, columns=spreads.columns)
    for col in spreads.columns:
        sp = spreads[col]
        mu = sp.rolling(z_window).mean()
        sd = sp.rolling(z_window).std().replace(0, np.nan)
        z = ((sp - mu) / sd).ffill()
        state = np.zeros(len(z))
        for i in range(1, len(z)):
            zi = z.iloc[i]
            if np.isnan(zi):
                continue
            if state[i - 1] == 0:
                if zi > entry_z:
                    state[i] = -1  # curve steep -> bet on flattening (short spread)
                elif zi < -entry_z:
                    state[i] = 1   # curve flat/inverted -> bet on steepening (long spread)
            else:
                if abs(zi) < exit_z:
                    state[i] = 0
                else:
                    state[i] = state[i - 1]
        weights[col] = state

    # P&L is in absolute yield-change terms, not percent return of a price
    # series: P&L_t = pos_{t-1} * (spread_t - spread_{t-1}) in % of notional.
    # A custom loop is required (the generic engine is return-based).
    daily_ret = pd.Series(0.0, index=spreads.index)
    pos = pd.Series(0.0, index=spreads.columns)
    equity = 1.0
    eq_curve = []
    turnover_total = 0.0
    last_rebal = -999
    deltas = spreads.diff()
    for i, date in enumerate(spreads.index):
        if i > 0:
            # DV01-matched: 1bp spread move = 1bp P&L on capital -> scale by 0.01
            daily_ret.iloc[i] = (pos * deltas.iloc[i]).sum() * 0.01
            equity *= 1 + daily_ret.iloc[i]
        eq_curve.append(equity)
        if i - last_rebal >= rebalance_freq and i > 0 and i < len(spreads.index) - 1:
            w_target = weights.iloc[i].fillna(0.0)
            turn = (w_target - pos).abs().sum()
            turnover_total += turn
            equity -= turn * cost_bps / 10000.0 * equity
            pos = w_target.copy()
            last_rebal = i
    eq_series = pd.Series(eq_curve, index=spreads.index)
    daily_ret = daily_ret.iloc[1:]
    perf = compute_performance(daily_ret, eq_series.iloc[1:], benchmark_returns=None,
                               n_trades=int(turnover_total / 2), turnover_total=turnover_total)
    print(perf.summary())
    return perf, weights


if __name__ == "__main__":
    perf, w = run_fi_arb()
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    perf.equity_curve.to_csv(out / "equity_FI_Arb_curve.csv")
    print("  Saved equity curve")
