"""Long/Short market-neutral backtesting framework — hyperparameter-driven.

Every tunable knob lives in `config.Config` (90+ fields).  Run experiments
via the runner CLI or the experiment harness (grid / random / parallel).

Pipeline modules:
  data              -- load + align equity panel + macro (VIX)
  factors           -- 14 base alpha factors + 5 extra factors
  ic_screen         -- rolling RankIC + ICIR + Bonferroni gate
  model             -- rolling OLS / ICIR-weighted ensemble + OOS prediction
  optimizer         -- mean-var / risk-parity / equal-weight with scipy SLSQP
  portfolio         -- L/S sleeve selection + turnover control
  backtest          -- event-driven, T+1 execution, VIX de-risking, vol-target
  diagnostics       -- regime split + window sweep + weight stability
  sharpe_gate       -- pre-backtest Sharpe estimator (skip if predicted < 1.5)
  high_sharpe_strategies -- 11 named strategy variants for parallel search
  experiment        -- grid / random / parallel sweep harness (multiprocessing)
  runner            -- end-to-end orchestrator + CLI + artifact export

Future-function guard raises FutureFunctionError immediately on detection.
Smoke tests: python -m tools.quant.ls.test_smoke
"""
from .config import Config, ConfigError

__all__ = ["Config", "ConfigError",
           "data", "factors", "ic_screen", "model", "portfolio",
           "optimizer", "backtest", "diagnostics", "sharpe_gate",
           "high_sharpe_strategies", "experiment", "runner"]
