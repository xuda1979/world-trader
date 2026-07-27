"""Pre-backtest Sharpe ratio estimator / quality gate.

Goal: avoid running expensive backtests on strategies we expect to have
Sharpe < 1.5.  We estimate the *expected* Sharpe BEFORE the backtest using
Grinold's fundamental law of active management:

  IR ≈ IC * sqrt(BR)

where:
  IC = cross-sectional information coefficient (mean rank IC of combined signal)
  BR = breadth = number of independent bets per year

For a daily-rebalanced L/S over N names with h-day forward returns:
  BR ≈ N_independent * (252 / h)
  IC_annual ≈ mean_daily_IC * sqrt(252)   [if daily IC obs]
  predicted_sharpe ≈ IC_annual * sqrt(BR) * signal_to_noise_ratio

We use the rolling ICIR of the COMBINED factor signal (from the training
window) as the IC estimate.  This is more honest than per-factor ICIR
because it accounts for cross-factor correlation.

If `predicted_sharpe < sharpe_gate_threshold`, the gate raises
SharpeGateError (or returns False), and the runner skips the backtest.

We also expose a function to *estimate* the achievable Sharpe from the
factors alone, so the user can see how close the current factor set is to
the 1.5 target.
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class SharpeGateError(Exception):
    """Raised when predicted Sharpe < required threshold."""
    pass


def estimate_predicted_sharpe(ic_series: pd.Series, n_universe: int,
                              horizon: int = 5, independent_frac: float = 0.5
                              ) -> Dict[str, float]:
    """Estimate expected annualized Sharpe from a combined IC time series.

    ic_series:     Series of cross-sectional rank ICs of the COMBINED signal
                   (one value per rebalance).  Must cover a meaningful sample.
    n_universe:    number of tickers in the cross-section.
    horizon:       forward-return horizon in days.
    independent_frac: fraction of the universe that is "independent" bets
                      (0.5 default = ~half the names carry independent signal;
                       the rest are correlated).  Conservative.

    Returns dict with:
      mean_ic, std_ic, icir, n_obs, breadth, predicted_sharpe, predicted_sharpe_conservative
    """
    ic = ic_series.dropna()
    n_obs = len(ic)
    if n_obs < 10:
        return {"mean_ic": np.nan, "std_ic": np.nan, "icir": np.nan,
                "n_obs": n_obs, "breadth": 0, "predicted_sharpe": 0.0,
                "predicted_sharpe_conservative": 0.0, "status": "insufficient_obs"}
    mean_ic = float(ic.mean())
    std_ic = float(ic.std(ddof=0))
    icir = float(mean_ic / std_ic) if std_ic > 0 else 0.0
    # Breadth: independent bets per year
    # Daily IC obs -> 252/horizon independent cross-sections per year
    # Each cross-section has ~independent_frac * n_universe independent bets
    n_indep = max(1, int(n_universe * independent_frac))
    breadth = n_indep * (252.0 / horizon)
    # Grinold: IR = IC * sqrt(BR).  Here IC is the *mean* IC (not ICIR).
    # Annualized Sharpe from daily IC:  Sharpe = mean_ic * sqrt(BR)
    predicted_sharpe = float(mean_ic * np.sqrt(breadth))
    # Conservative: use ICIR (which accounts for IC volatility) and haircut
    # for transaction costs / estimation error
    predicted_sharpe_conservative = float(icir * np.sqrt(breadth) * 0.5)  # 50% haircut
    return {
        "mean_ic": mean_ic, "std_ic": std_ic, "icir": icir, "n_obs": n_obs,
        "breadth": float(breadth), "n_independent": n_indep,
        "predicted_sharpe": predicted_sharpe,
        "predicted_sharpe_conservative": predicted_sharpe_conservative,
        "status": "ok",
    }


def estimate_from_factors(ic_df: pd.DataFrame, kept_factors: List[str],
                          n_universe: int, horizon: int = 5,
                          independent_frac: float = 0.5) -> Dict[str, float]:
    """Estimate predicted Sharpe from per-factor IC time series.

    We form a simple equal-weight combination of the kept factors' ICs
    (proxy for the combined signal IC), then apply Grinold's law.
    """
    if not kept_factors:
        return {"predicted_sharpe": 0.0, "status": "no_factors"}
    cols = [c for c in kept_factors if c in ic_df.columns]
    if not cols:
        return {"predicted_sharpe": 0.0, "status": "no_ic_data"}
    combined_ic = ic_df[cols].mean(axis=1)  # equal-weight proxy
    return estimate_predicted_sharpe(combined_ic, n_universe, horizon, independent_frac)


def quality_gate(estimate: Dict[str, float], threshold: float = 1.5
                 ) -> Tuple[bool, str]:
    """Decide whether to proceed with the backtest.

    Returns (proceed, reason).  We use the *conservative* estimate.
    """
    pred = estimate.get("predicted_sharpe_conservative", 0.0)
    if not np.isfinite(pred):
        return False, f"predicted Sharpe not finite ({pred})"
    if pred < threshold:
        return False, (f"predicted Sharpe {pred:.2f} < threshold {threshold:.2f}; "
                       f"skip backtest.  Consider: (1) add stronger factors, "
                       f"(2) lower icir_threshold to include more factors, "
                       f"(3) expand the universe for more breadth.")
    return True, (f"predicted Sharpe {pred:.2f} >= threshold {threshold:.2f}; "
                  f"proceed with backtest.")
