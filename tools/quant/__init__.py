"""Renaissance Technologies–style statistical arbitrage system.

A multi-signal, market-neutral quant framework with rigorous walk-forward
backtesting and multiple-testing correction.  Designed to run on synthetic
data (offline) or real price data (when internet is available).

Modules
-------
synth        – synthetic-data generators (GBM, OU mean-reversion, jumps)
features     – feature engineering (returns, rolling stats, PCA, Hurst,
                half-life, z-scores)
signals      – signal generation (pairs trading, OU mean reversion,
                cross-sectional momentum/reversion)
portfolio    – portfolio construction (market-neutral, risk-parity, Kelly)
backtest     – vectorized backtesting engine + walk-forward + DSR
risk         – risk management (VaR, drawdown, position/leverage limits)
reporting    – performance metrics, equity curves, tear sheet
cli          – command-line entry point
"""
__version__ = "1.0.0"
