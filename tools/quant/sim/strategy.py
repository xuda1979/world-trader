"""Strategy base class + setup-library adapter.

A strategy is a callable that receives a stream of bars (plus a context
holding the current portfolio / broker / time) and emits ``Signal`` objects.
The simulator's runner handles turning signals into orders via the
portfolio.

We provide one concrete strategy out of the box:

  * ``SetupLibraryStrategy`` -- wraps ``wt.analysis.scan_setups`` so the
    simulator can trade the EXACT same setup library the daily scanner
    uses.  This is the key bridge: any setup that passes the scanner's
    statistical gates can be paper-traded here on real-time data.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional

from .events import Bar, Order, Position, Side, Signal


@dataclass
class StrategyContext:
    """What the strategy sees on each bar.

    * ``bar``       -- the current bar
    * ``portfolio`` -- the Portfolio (positions, cash, equity)
    * ``broker``    -- the SimBroker (for querying last quotes)
    * ``clock``     -- current sim time (Unix seconds)
    * ``history``   -- per-symbol deque of recent bars (lookback window)
    """
    bar: Bar
    portfolio: "object"            # forward ref to Portfolio
    broker: "object"               # forward ref to SimBroker
    clock: float
    history: Dict[str, Deque[Bar]]


class Strategy:
    """Base class.  Override ``on_bar(ctx)`` to emit Signals."""

    name: str = "base"

    def on_bar(self, ctx: StrategyContext) -> List[Signal]:
        raise NotImplementedError

    def on_fill(self, fill, ctx: StrategyContext) -> None:
        """Optional: called when a fill happens (for tracking)."""
        pass

    def on_session_end(self, ctx: StrategyContext) -> None:
        """Optional: called once when the feed is exhausted."""
        pass


# ------------------------------------------------------- setup library --
class SetupLibraryStrategy(Strategy):
    """Trade the wt.analysis setup library on each new bar.

    Accumulates bars into a rolling window per symbol, then calls
    ``analysis.scan_setups`` on each bar.  When a setup fires AND passes the
    statistical gate (``analysis.trade_qualifies``), emit a Signal with the
    concrete trade plan (entry/stop/target/risk/reward) from
    ``analysis.rr_from_setup``.

    Parameters
    ----------
    lookback : int
        number of bars of history to retain per symbol (must be >= 200 for
        sma200-based setups to work).
    market : str
        market tag passed to scan_setups (US/CN/HK/CRYPTO/FX/DEFAULT).
    require_qualifies : bool
        if True (default), only emit signals for setups that pass the
        statistical gate.  Set False to see ALL firing setups (useful when
        developing / stress-testing).
    per_symbol_limit : int
        max concurrent signals per symbol (1 = no stacking).
    horizon : int
        max-bars-to-hold for emitted signals.
    """
    name = "SetupLibrary"

    def __init__(self, lookback: int = 260, market: str = "US",
                 require_qualifies: bool = True, per_symbol_limit: int = 1,
                 horizon: int = 5):
        self.lookback = max(lookback, 260)
        self.market = market
        self.require_qualifies = require_qualifies
        self.per_symbol_limit = per_symbol_limit
        self.horizon = horizon
        self._hist: Dict[str, Deque[Bar]] = {}

    def on_bar(self, ctx: StrategyContext) -> List[Signal]:
        bar = ctx.bar
        dq = self._hist.setdefault(bar.symbol, deque(maxlen=self.lookback))
        dq.append(bar)
        # Need at least 200 bars for sma200-based setups.
        if len(dq) < 210:
            return []
        # Respect per-symbol concurrent-position limit.
        pos = ctx.portfolio.positions.get(bar.symbol)
        if pos is not None and not pos.is_flat:
            return []

        signals = self._scan_symbol(bar, dq)
        return signals

    def _scan_symbol(self, bar: Bar, dq: Deque[Bar]) -> List[Signal]:
        # Local import to avoid a hard dep at module load time.
        try:
            from .. import analysis as A  # type: ignore
        except Exception:
            # ``wt.analysis`` lives in tools/wt, not tools/quant; we import
            # it lazily through the tools path the runner sets up.
            import sys
            try:
                from wt import analysis as A  # type: ignore
            except Exception:
                return []
        highs = [b.high for b in dq]
        lows = [b.low for b in dq]
        closes = [b.close for b in dq]
        opens = [b.open for b in dq]
        vols = [b.volume for b in dq]
        # scan_setups returns the BEST setup per name (only firing ones by
        # default).  Each entry has the backtest stat dict + the setup def.
        try:
            out = A.scan_setups(highs, lows, closes, opens=opens,
                                volumes=vols, market=self.market,
                                require_firing=True)
        except Exception:
            return []
        signals: List[Signal] = []
        for sd in out:
            bt = sd.get("bt") or sd
            if self.require_qualifies and not A.trade_qualifies(bt):
                continue
            side = Side.LONG if sd.get("side", "Long") == "Long" else Side.SHORT
            # Build a concrete trade plan off the current close.
            try:
                rr = A.rr_from_setup(bar.close, sd)
            except Exception:
                rr = None
            if rr is None:
                continue
            sig = Signal(
                ts=bar.ts, symbol=bar.symbol, side=side,
                setup=sd.get("name", "unknown"),
                strength=1.0,
                entry=rr.get("entry"),
                stop=rr.get("stop"),
                target=rr.get("target"),
                horizon=self.horizon,
                meta={"rr": rr.get("rr"), "risk": rr.get("risk"),
                      "reward": rr.get("reward"),
                      "exp_ret": bt.get("exp_ret"),
                      "edge": bt.get("edge"),
                      "oos_edge": bt.get("oos_edge")},
            )
            signals.append(sig)
        return signals
