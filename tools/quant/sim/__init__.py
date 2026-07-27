"""Real-time simulation engine for the world-trader quant framework.

Event-driven, bar-by-bar simulator that can:

  * Replay historical data through a strategy (offline validation on real
    price history, not just synthetic data).
  * Run on a live data feed (polls ``wt.sources`` on a tick) so strategies
    can be tested against real-time market data without risking capital.
  * Plug into the existing setup library in ``wt.analysis`` (the same
    signals that power the daily scanner) so we validate the EXACT trade
    rules we intend to deploy.

Modules
-------
events      – dataclasses: Bar, Tick, Signal, Order, Fill, Position
broker      – simulated broker: fills, slippage, commission, stop/target
data_feed   – live/replay data feed abstraction over ``wt.sources``
strategy    – Strategy base class + ``SetupLibraryStrategy`` adapter
portfolio   – position + cash + equity tracker (mark-to-market)
metrics     – performance metrics aligned with ``analysis._stats`` / DSR
runner      – the main simulation loop (live or replay)
cli         – command-line entry point

The design mirrors a production execution stack (feed -> strategy -> broker
-> portfolio) so a strategy developed here can be promoted to a paper-trading
or live-trading harness with minimal changes.
"""
from .events import (
    Bar, Tick, Signal, Order, Fill, Position, Side, OrderType, OrderStatus,
)
from .broker import SimBroker, BrokerConfig
from .data_feed import (
    DataFeed, ReplayFeed, LiveFeed, FeedEvent, BarEvent, TickEvent,
)
from .strategy import Strategy, SetupLibraryStrategy, StrategyContext
from .portfolio import Portfolio, PortfolioConfig
from .metrics import perf_stats, sharpe, max_drawdown, deflated_sharpe
from .runner import Simulator, SimulatorResult, run_backtest, run_live

__all__ = [
    "Bar", "Tick", "Signal", "Order", "Fill", "Position",
    "Side", "OrderType", "OrderStatus",
    "SimBroker", "BrokerConfig",
    "DataFeed", "ReplayFeed", "LiveFeed",
    "FeedEvent", "BarEvent", "TickEvent",
    "Strategy", "SetupLibraryStrategy", "StrategyContext",
    "Portfolio", "PortfolioConfig",
    "perf_stats", "sharpe", "max_drawdown", "deflated_sharpe",
    "Simulator", "SimulatorResult", "run_backtest", "run_live",
]

__version__ = "0.1.0"
