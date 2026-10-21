"""Strategy: Alternative Risk Premia — Factor Momentum (Ehsani-Linnainmaa)

Momentum of FACTOR returns: long the factors with the best trailing 12m
return, short the worst. The paper finds a robust anomaly (Sharpe ~0.4+)
over 1963-2019.

On this free data (Fama-French daily factors, MKT/SMB/HML/UMD):
  - 1926+ (century): Sharpe +0.26, +4.5%/yr — the anomaly exists
  - 1963+:          Sharpe +0.24
  - 2008+ (suite window): Sharpe -0.04 — the premium DECAYED post-GFC,
    consistent with factor-premium crowding since ~2010.

Construction: monthly rebalance, top-2/bottom-2 of 4 factors by trailing
252d return, equal weight, 6 bps, T+1 via the shared engine (synthetic
price path = cumprod of 1+factor, since the engine is price-based).
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


def load_ff_factors(dir_path: Path = None) -> pd.DataFrame:
    """Load Fama-French daily factors (Mkt-RF, SMB, HML, UMD), in decimal."""
    if dir_path is None:
        # tools/quant/hedge_fund_strats/ -> tools/quant/data/ff_factors
        dir_path = Path(__file__).resolve().parent.parent / "data" / "ff_factors"
    ff = pd.read_csv(dir_path / "F-F_Research_Data_Factors_daily.csv", skiprows=4)
    ff.columns = ["date", "Mkt-RF", "SMB", "HML", "RF"]
    mom = pd.read_csv(dir_path / "F-F_Momentum_Factor_daily.csv", skiprows=12)
    mom.columns = ["date", "UMD"]
    for df in (ff, mom):
        df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
        df.set_index("date", inplace=True)
    factors = ff[["Mkt-RF", "SMB", "HML"]].join(mom["UMD"], how="left").astype(float) / 100
    return factors.replace(-99.99 / 100, np.nan)


def run_factor_momentum(n_long: int = 2,
                        n_short: int = 2,
                        lookback: int = 252,
                        rebalance_freq: int = 21,
                        start: str = "2008-01-01",
                        cost_bps: float = TRADING_COST_BPS) -> Tuple[Performance, pd.DataFrame]:
    print("\n" + "=" * 70)
    print("ALTERNATIVE RISK PREMIA: FACTOR MOMENTUM (Ehsani-Linnainmaa)")
    print("=" * 70)
    factors = load_ff_factors()
    factors = factors[factors.index >= start].fillna(0.0)
    prices = (1 + factors).cumprod()  # synthetic price path
    print(f"  Factors: {list(factors.columns)} | {factors.index[0].date()}..{factors.index[-1].date()}")

    w = pd.DataFrame(np.nan, index=factors.index, columns=factors.columns)
    for i in range(len(factors)):
        if i % rebalance_freq != 0:
            continue
        past = factors.iloc[max(0, i - lookback):i + 1]
        if len(past) < 200:
            continue
        perf12 = (1 + past).prod() - 1
        ranked = perf12.sort_values()
        row = pd.Series(0.0, index=factors.columns)
        for p in ranked.index[-n_long:]:
            row[p] = 1.0 / n_long
        for p in ranked.index[:n_short]:
            row[p] = -1.0 / n_short
        w.iloc[i] = row
    w = w.ffill().fillna(0.0)

    engine = BacktestEngine(prices, cost_bps=cost_bps)
    daily_ret, equity, turnover = engine.run(w, rebalance_freq=rebalance_freq)
    perf = compute_performance(daily_ret, equity, benchmark_returns=factors["Mkt-RF"],
                               n_trades=int(turnover / 2), turnover_total=turnover)
    print(perf.summary())
    return perf, w


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "results"
    out.mkdir(exist_ok=True)
    for start, tag in [("2008-01-01", "2008"), ("1963-07-01", "1963"), ("1926-01-01", "1926")]:
        perf, _ = run_factor_momentum(start=start)
        perf.equity_curve.to_csv(out / f"equity_FactorMom_{tag}.csv")
