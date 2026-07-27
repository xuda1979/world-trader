"""High-Sharpe strategy variants for parallel experimentation.

Each function returns a Config tuned for a specific hypothesis.  We run
them all in parallel and pick the best.

Hypotheses:
  1. momentum_value:    momentum + value (MA deviation) combo
  2. reversal_focus:    short-term reversal dominant
  3. vol_low_vol:       low-vol anomaly (long low-vol, short high-vol)
  4. liquidity_premium: long illiquid, short liquid (or vice versa)
  5. trend_follow:      MA-50 / MA-200 trend signals
  6. multi_factor_icir: all 4 significant factors, ICIR-weighted
  7. concentrated_ls:   3+3 names, high leverage, vol-targeted
  8. daily_rebalance:   refit every day, rebalance every day (cost-aware)
  9. long_horizon:      10-day forward returns (more signal, less turnover)
  10. short_horizon:    3-day forward returns (faster signal decay)
"""
from __future__ import annotations
import os, sys
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from .config import Config


def baseline_high_sharpe() -> Config:
    return Config().copy(**{
        "name": "hs_baseline",
        "model_method": "icir",
        "icir_threshold": 0.10, "ic_mean_threshold": 0.005,
        "ic_bonferroni": False,
        "n_long": 5, "n_short": 5,
        "weighting": "mean_var", "opt_lambda_risk": 2.0,
        "position_cap_pct": 0.25, "gross_leverage": 1.5,
        "vol_target_active": True, "vol_target_annual": 0.12,
        "train_window": 120, "refit_freq": 5, "rebalance_freq": 5,
        "model_weight_smooth": 0.5, "beta_max_abs": 0.10,
        "sharpe_gate_enabled": True, "sharpe_gate_threshold": 1.5,
        "cost_bps_one_side": 5.0,
    })


def momentum_value() -> Config:
    """Momentum (12-1m) + trend (MA-200 deviation)."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_momentum_value",
        "n_long": 8, "n_short": 8,
        "gross_leverage": 1.8,
        "vol_target_annual": 0.13,
        "opt_lambda_risk": 1.5,
        "model_weight_smooth": 0.3,
    })


def reversal_focus() -> Config:
    """Short-term reversal dominant (1w, 3w)."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_reversal_focus",
        "n_long": 10, "n_short": 10,
        "gross_leverage": 1.5,
        "vol_target_annual": 0.11,
        "predict_horizon": 3, "return_horizon_fwd": 3,
        "rebalance_freq": 3, "refit_freq": 3,
        "model_weight_smooth": 0.2,
    })


def low_vol_anomaly() -> Config:
    """Long low-vol, short high-vol (low-vol anomaly)."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_low_vol",
        "n_long": 8, "n_short": 8,
        "gross_leverage": 1.5,
        "vol_target_annual": 0.10,
        "opt_lambda_risk": 3.0,  # more risk-averse
        "position_cap_pct": 0.20,
        "train_window": 140,
    })


def liquidity_premium() -> Config:
    """Liquidity factor dominant."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_liquidity",
        "n_long": 10, "n_short": 10,
        "gross_leverage": 1.5,
        "vol_target_annual": 0.12,
        "opt_lambda_risk": 1.0,
        "model_weight_smooth": 0.4,
    })


def trend_follow() -> Config:
    """MA-50 / MA-200 trend signals."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_trend",
        "n_long": 7, "n_short": 7,
        "gross_leverage": 1.6,
        "vol_target_annual": 0.12,
        "predict_horizon": 10, "return_horizon_fwd": 10,
        "rebalance_freq": 10, "refit_freq": 10,
        "model_weight_smooth": 0.5,
    })


def multi_factor_icir() -> Config:
    """All 4 significant factors, ICIR-weighted, balanced."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_multi_factor",
        "n_long": 6, "n_short": 6,
        "gross_leverage": 1.7,
        "vol_target_annual": 0.14,
        "opt_lambda_risk": 1.5,
        "train_window": 100, "refit_freq": 5,
    })


def concentrated_ls() -> Config:
    """3+3 names, high leverage, vol-targeted to 15%."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_concentrated",
        "n_long": 3, "n_short": 3,
        "gross_leverage": 2.0,
        "vol_target_annual": 0.15,
        "position_cap_pct": 0.35,
        "opt_lambda_risk": 1.0,
        "beta_max_abs": 0.15,
    })


def daily_rebalance() -> Config:
    """Daily refit + daily rebalance (cost-aware)."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_daily",
        "n_long": 8, "n_short": 8,
        "gross_leverage": 1.5,
        "vol_target_annual": 0.12,
        "refit_freq": 1, "rebalance_freq": 1,
        "cost_bps_one_side": 4.0,  # tight cost assumption
        "model_weight_smooth": 0.6,  # heavy smoothing to avoid churn
        "turnover_threshold_diff": 0.002,  # higher cost-gate
    })


def long_horizon() -> Config:
    """10-day forward returns."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_long_horizon",
        "n_long": 8, "n_short": 8,
        "gross_leverage": 1.6,
        "vol_target_annual": 0.13,
        "predict_horizon": 10, "return_horizon_fwd": 10,
        "rebalance_freq": 10, "refit_freq": 5,
    })


def short_horizon() -> Config:
    """3-day forward returns."""
    return baseline_high_sharpe().copy(**{
        "name": "hs_short_horizon",
        "n_long": 8, "n_short": 8,
        "gross_leverage": 1.5,
        "vol_target_annual": 0.11,
        "predict_horizon": 3, "return_horizon_fwd": 3,
        "rebalance_freq": 3, "refit_freq": 3,
        "model_weight_smooth": 0.2,
    })


def all_strategies() -> List[Tuple[str, Config]]:
    """Return all 10 high-Sharpe strategy variants."""
    return [
        ("hs_baseline", baseline_high_sharpe()),
        ("hs_momentum_value", momentum_value()),
        ("hs_reversal_focus", reversal_focus()),
        ("hs_low_vol", low_vol_anomaly()),
        ("hs_liquidity", liquidity_premium()),
        ("hs_trend", trend_follow()),
        ("hs_multi_factor", multi_factor_icir()),
        ("hs_concentrated", concentrated_ls()),
        ("hs_daily", daily_rebalance()),
        ("hs_long_horizon", long_horizon()),
        ("hs_short_horizon", short_horizon()),
    ]
