"""The simulation loop: feed -> strategy -> broker -> portfolio.

Provides:
  * ``Simulator`` -- the core engine.  Holds a broker, portfolio, strategy,
    and one or more feeds.  On each bar: advances the portfolio's clock,
    checks bracket exits, asks the strategy for signals, turns signals
    into orders, submits them to the broker, and fills them.
  * ``run_backtest`` -- convenience: replay one symbol's history through a
    strategy and return the PerfStats.
  * ``run_live`` -- convenience: poll a live fetcher and run the same loop
    until the feed is exhausted (or interrupted).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

from .broker import BrokerConfig, SimBroker
from .data_feed import DataFeed, LiveFeed, ReplayFeed
from .events import Bar, Fill, Order, OrderStatus, OrderType, Position, Side, Signal
from .metrics import PerfStats, perf_stats
from .portfolio import Portfolio, PortfolioConfig
from .strategy import SetupLibraryStrategy, Strategy, StrategyContext


@dataclass
class SimulatorResult:
    """Returned by ``Simulator.run()``."""
    stats: PerfStats
    fills: List[Fill]
    orders: List[Order]
    equity_curve: List[tuple]
    trade_returns: List[float]
    n_bars: int
    final_equity: float


class Simulator:
    """Core event-driven simulation engine.

    Single-symbol by default; multi-symbol support via ``add_feed``.

    Usage:
        sim = Simulator(strategy=SetupLibraryStrategy(market="US"),
                        broker_config=BrokerConfig(commission_bps=0.8))
        sim.add_feed(ReplayFeed("AAPL", ohlcv_dict))
        result = sim.run()
    """

    def __init__(self, strategy: Optional[Strategy] = None,
                 broker_config: Optional[BrokerConfig] = None,
                 portfolio_config: Optional[PortfolioConfig] = None,
                 periods_per_year: int = 252,
                 n_trials: int = 1):
        self.strategy = strategy or SetupLibraryStrategy()
        self.broker = SimBroker(broker_config)
        self.portfolio = Portfolio(portfolio_config
                                   or PortfolioConfig())
        self.feeds: List[DataFeed] = []
        self.periods_per_year = periods_per_year
        self.n_trials = n_trials
        # All orders/fills ever submitted (for post-run analysis).
        self._all_orders: List[Order] = []
        self._trade_returns: List[float] = []
        self._last_equity_at_entry: Dict[str, float] = {}
        self._bar_count = 0
        self._on_bar_callbacks: List[Callable] = []

    def add_feed(self, feed: DataFeed) -> "Simulator":
        self.feeds.append(feed)
        return self

    def on_bar_callback(self, fn: Callable) -> None:
        """Register a callback ``fn(bar, portfolio, broker)`` for each bar."""
        self._on_bar_callbacks.append(fn)

    def run(self) -> SimulatorResult:
        """Run the full simulation.  Returns a SimulatorResult."""
        if not self.feeds:
            return SimulatorResult(
                stats=PerfStats(), fills=[], orders=[], equity_curve=[],
                trade_returns=[], n_bars=0,
                final_equity=self.portfolio.cash,
            )
        # Single-feed fast path; multi-feed would require a merge by ts.
        if len(self.feeds) == 1:
            for bar in self.feeds[0]:
                self._step(bar)
        else:
            # Merge by ts: pull from all feeds in time order.
            import heapq
            its = [iter(f) for f in self.feeds]
            heap = []
            for i, it in enumerate(its):
                try:
                    b = next(it)
                    heapq.heappush(heap, (b.ts, i, b, it))
                except StopIteration:
                    pass
            while heap:
                ts, i, b, it = heapq.heappop(heap)
                self._step(b)
                try:
                    nb = next(it)
                    heapq.heappush(heap, (nb.ts, i, nb, it))
                except StopIteration:
                    pass

        # End-of-session hook.
        ctx = StrategyContext(
            bar=Bar(symbol="", ts=0, open=0, high=0, low=0, close=0),
            portfolio=self.portfolio, broker=self.broker, clock=0,
            history={},
        )
        try:
            self.strategy.on_session_end(ctx)
        except Exception:
            pass

        # Final mark.
        prices = {sym: b.close for sym, b in self.broker._last_bar.items()}
        eq = self.portfolio.mark(prices, ts=0)
        # Build stats.
        eq_only = [e for _, e in self.portfolio.equity_curve]
        rets = [eq_only[i] / eq_only[i - 1] - 1.0
                for i in range(1, len(eq_only)) if eq_only[i - 1] != 0]
        stats = perf_stats(rets, eq_only, n_trials=self.n_trials,
                           periods_per_year=self.periods_per_year,
                           trade_returns=self._trade_returns or None)
        return SimulatorResult(
            stats=stats,
            fills=list(self.broker.fills),
            orders=list(self._all_orders),
            equity_curve=list(self.portfolio.equity_curve),
            trade_returns=list(self._trade_returns),
            n_bars=self._bar_count,
            final_equity=eq,
        )

    # ----------------------------------------------------------- one bar --
    def _step(self, bar: Bar) -> None:
        self._bar_count += 1
        # 1) Check bracket exits on existing positions BEFORE the strategy
        #    sees the bar (the bracket fires on this bar's high/low).
        bracket_fills = self.broker.check_brackets(self.portfolio.positions, bar)
        for f in bracket_fills:
            self._realize_trade(f, bar)

        # 2) Also check time-based exits (max-horizon).
        expired = self.portfolio.tick_horizons()
        for sym in expired:
            pos = self.portfolio.positions.get(sym)
            if pos is None or pos.is_flat:
                continue
            # Flatten at the bar's close.
            close_side = Side.SHORT if pos.is_long else Side.LONG
            order = Order(
                ts=bar.ts, symbol=sym, side=close_side, qty=abs(pos.qty),
                order_type=OrderType.MARKET, tag=f"horizon:{pos.setup}",
            )
            self.broker.submit(order)
            self._all_orders.append(order)

        # 3) Fill any pending orders (including the horizon exits above)
        #    against this bar.
        fills = self.broker.on_bar(bar)
        for f in fills:
            self._realize_trade(f, bar)

        # 4) Ask the strategy for new signals.
        prices = {sym: b.close for sym, b in self.broker._last_bar.items()}
        eq = self.portfolio.mark(prices, ts=bar.ts)
        ctx = StrategyContext(
            bar=bar, portfolio=self.portfolio, broker=self.broker,
            clock=bar.ts, history={},
        )
        try:
            signals = self.strategy.on_bar(ctx) or []
        except Exception:
            signals = []
        for sig in signals:
            self._handle_signal(sig, bar, eq)

        # 5) On-bar callbacks (e.g. logging).
        for cb in self._on_bar_callbacks:
            try:
                cb(bar, self.portfolio, self.broker)
            except Exception:
                pass

    def _handle_signal(self, sig: Signal, bar: Bar, equity: float) -> None:
        qty = self.portfolio.size_for_signal(sig, equity, bar.close)
        if qty is None or qty <= 0:
            return
        order = self.portfolio.build_order(sig, qty, ts=bar.ts)
        self.broker.submit(order)
        self._all_orders.append(order)
        # Track entry equity for trade-return accounting.
        self._last_equity_at_entry[sig.symbol] = equity

    def _realize_trade(self, fill: Fill, bar: Bar) -> None:
        """Apply a fill to the portfolio and record a trade return when a
        position is closed."""
        # Was this a closing fill?  Heuristic: if the position for this
        # symbol becomes flat after the fill, record a trade return.
        pre_pos = self.portfolio.positions.get(fill.symbol)
        pre_qty = pre_pos.qty if pre_pos else 0.0
        self.portfolio.apply_fill(fill)
        # Attach bracket if the fill opened a position and we have a signal
        # with stop/target -- the portfolio doesn't know about signals, so
        # we rely on the order's take_profit/stop_loss being set.
        # We look up the originating order for the bracket levels.
        if fill.order_id:
            for o in self._all_orders:
                if o.order_id == fill.order_id:
                    if o.take_profit is not None or o.stop_loss is not None:
                        self.portfolio.attach_bracket_to_position(
                            fill.symbol, o.stop_loss, o.take_profit)
                    # set horizon
                    pos = self.portfolio.positions.get(fill.symbol)
                    if pos and not pos.is_flat and o.tag:
                        pos.setup = o.tag
                        pos.horizon = getattr(self.strategy, "horizon", 0)
                    break
        # If position is now flat, record a trade return.
        post_pos = self.portfolio.positions.get(fill.symbol)
        if (post_pos is None or post_pos.is_flat) and not abs(pre_qty) < 1e-9:
            eq_now = self.portfolio.equity(
                {s: b.close for s, b in self.broker._last_bar.items()})
            entry_eq = self._last_equity_at_entry.pop(fill.symbol, None)
            if entry_eq and entry_eq > 0:
                self._trade_returns.append(eq_now / entry_eq - 1.0)


# --------------------------------------------------------------- helpers --
def run_backtest(symbol: str, bars, strategy: Optional[Strategy] = None,
                 broker_config: Optional[BrokerConfig] = None,
                 portfolio_config: Optional[PortfolioConfig] = None,
                 timeframe: str = "1d",
                 periods_per_year: int = 252) -> SimulatorResult:
    """One-shot: replay ``bars`` (OHLCV dict or list of Bar) through a
    strategy and return the SimulatorResult."""
    sim = Simulator(strategy=strategy, broker_config=broker_config,
                    portfolio_config=portfolio_config,
                    periods_per_year=periods_per_year)
    sim.add_feed(ReplayFeed(symbol, bars, timeframe=timeframe))
    return sim.run()


def run_live(symbol: str, fetcher: Callable[[], Optional[dict]],
             strategy: Optional[Strategy] = None,
             broker_config: Optional[BrokerConfig] = None,
             portfolio_config: Optional[PortfolioConfig] = None,
             interval_sec: float = 60.0, max_bars: int = 10_000,
             timeframe: str = "1d",
             periods_per_year: int = 252) -> SimulatorResult:
    """One-shot: poll ``fetcher`` on a cadence and run the loop until the
    feed is exhausted (or ``max_bars`` is hit).  Designed for real-time
    strategy validation on live market data."""
    sim = Simulator(strategy=strategy, broker_config=broker_config,
                    portfolio_config=portfolio_config,
                    periods_per_year=periods_per_year)
    sim.add_feed(LiveFeed(symbol, fetcher, interval_sec=interval_sec,
                          max_bars=max_bars, timeframe=timeframe))
    return sim.run()
