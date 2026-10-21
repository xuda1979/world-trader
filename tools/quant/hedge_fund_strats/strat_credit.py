"""Strategy: Credit Strategies (补充说明 category) — credit spread mean reversion

The classic credit trade: when the credit risk premium is stretched WIDE
(|z| > entry), credit is cheap -> buy it (long BAA, short AAA/10y); when it
is TIGHT, credit is expensive -> short it. Exit when |z| < exit.

Spreads used (FRED, free, 1983+):
  - BAA - AAA   (Moody's quality spread; 'baa', 'aaa' series)
  - BAA - 10y   (credit spread over the risk-free curve; 'us10y' series)
  - HY OAS      (BofA HY option-adjusted spread; 2023+ short window only)

P&L is in spread-bp units (DV01-matched: 1bp spread move = 1bp P&L), same
convention as the FI arb strategy. z-window is long (120-250d) because
credit cycles move slowly; costs are negligible at these sizes.

Honest caveat: long credit = short tail risk (GFC/LTCM-style blowouts are
the drawdown risk); the short-credit side (selling insurance) is the other
half of the trade.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd

try:
    from .core import compute_performance, Performance, TRADING_COST_BPS
except ImportError:  # run as script
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from core import compute_performance, Performance, TRADING_COST_BPS


def load_series(dir_path: Path = None) -> pd.DataFrame:
    if dir_path is None:
        dir_path = Path(__file__).resolve().parent / "data_fred"
    out = {}
    for name in ("aaa", "baa", "us10y", "hy_oas"):
        p = dir_path / f"{name}.csv"
        if p.exists():
            df = pd.read_csv(p, parse_dates=["date"], index_col="date")
            out[name] = df["value"]
    return pd.DataFrame(out)


def run_credit(z_window: int = 120,
               entry_z: float = 1.5,
               exit_z: float = 0.5,
               rebalance_freq: int = 21,
               start: str = "2008-01-01",
               cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame, pd.DataFrame]:
    print("\n" + "=" * 70)
    print("CREDIT STRATEGIES: spread mean reversion")
    print("=" * 70)
    s = load_series()
    spreads = pd.DataFrame(index=s.index)
    if all(c in s.columns for c in ("baa", "aaa")):
        spreads["baa_aaa"] = s["baa"] - s["aaa"]
    if all(c in s.columns for c in ("baa", "us10y")):
        spreads["baa_10y"] = s["baa"] - s["us10y"]
    if "hy_oas" in s.columns:
        spreads["hy_oas"] = s["hy_oas"]
    spreads = spreads.dropna(how="all").ffill(limit=5)
    spreads = spreads[spreads.index >= start]
    # drop spreads with < 500 days in window
    spreads = spreads[[c for c in spreads.columns if spreads[c].count() > 500]]
    print(f"  Spreads: {spreads.shape[0]}d x {spreads.shape[1]} ({list(spreads.columns)}) "
          f"from {spreads.index[0].date()}")

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
                    state[i] = 1    # spread WIDE -> credit cheap -> long credit
                elif zi < -entry_z:
                    state[i] = -1   # spread TIGHT -> credit expensive -> short credit
            else:
                if abs(zi) < exit_z:
                    state[i] = 0
                else:
                    state[i] = state[i - 1]
        weights[col] = state

    # P&L loop (bp units, DV01-matched): P&L% = pos * dspread(%) * 0.01
    deltas = spreads.diff()
    daily_ret = pd.Series(0.0, index=spreads.index)
    pos = pd.Series(0.0, index=spreads.columns)
    equity = 1.0
    curve, tt, last_rebal = [], 0.0, -999
    for i, date in enumerate(spreads.index):
        if i > 0:
            daily_ret.iloc[i] = (pos * deltas.iloc[i]).sum() * 0.01
            equity *= 1 + daily_ret.iloc[i]
        curve.append(equity)
        if i - last_rebal >= rebalance_freq and i > 0 and i < len(spreads.index) - 1:
            wt = weights.iloc[i].fillna(0.0)
            t = (wt - pos).abs().sum()
            tt += t
            equity -= t * cost_bps / 10000.0 * equity
            pos = wt.copy()
            last_rebal = i
    eq_s = pd.Series(curve, index=spreads.index)
    perf = compute_performance(daily_ret.iloc[1:], eq_s.iloc[1:], benchmark_returns=None,
                               n_trades=int(tt / 2), turnover_total=tt)
    print(perf.summary())
    return perf, weights, spreads


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    for zw, tag in [(120, "z120"), (250, "z250")]:
        for start, stag in [("2008-01-01", "2008"), ("1986-01-01", "1986")]:
            try:
                perf, _, _ = run_credit(z_window=zw, start=start)
                perf.equity_curve.to_csv(out / f"equity_Credit_{tag}_{stag}.csv")
            except Exception as e:
                print(f"  {tag}/{stag} ERROR: {e}")
