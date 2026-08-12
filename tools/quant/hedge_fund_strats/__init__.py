"""Hedge fund strategy backtest framework.

Backtests 5 major hedge fund strategy categories:
  1. Long/Short Equity (L/S)
  2. Equity Market Neutral (EMN)
  3. Global Macro (multi-asset)
  4. Merger Arbitrage (event-driven proxy)
  5. Managed Futures / CTA (trend following)

All strategies use:
  - 6 bps round-trip trading cost
  - Daily rebalancing (or as specified)
  - Proper T+1 execution (signal today, trade tomorrow)
  - Risk management overlays
"""
