"""Event dataclasses for the simulation engine.

The simulator is event-driven: the feed emits Bar/Tick events, the strategy
turns them into Signals, the portfolio turns Signals into Orders, the broker
fills Orders and emits Fills.  Everything else is state held by the
portfolio / strategy / broker.

These dataclasses are intentionally simple ``@dataclass`` objects (no
behavior) so they serialize cleanly to JSON for persistence / debugging.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class Side(str, Enum):
    LONG = "Long"
    SHORT = "Short"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    PENDING = "pending"      # accepted by broker, not yet filled
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Bar:
    """One OHLCV bar (any timeframe).  ``ts`` is Unix seconds (UTC)."""
    symbol: str
    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    timeframe: str = "1d"     # "1d", "5m", "1m", ...

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.ts, tz=timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dt"] = self.dt.isoformat()
        d["side"] = d.get("side")
        return d


@dataclass
class Tick:
    """A quote/trade update.  Used for live feeds and intraday sim."""
    symbol: str
    ts: float
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: float = 0.0

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.ts, tz=timezone.utc)


@dataclass
class Signal:
    """Strategy output: a directional call on a symbol.

    The strategy may attach a concrete trade plan (entry/stop/target) which
    the broker can honor with a bracket order.  If ``entry`` is None the
    broker fills at the next bar open.  ``strength`` in [0,1] is a
    confidence weight used for position sizing (Kelly fraction).
    """
    ts: float
    symbol: str
    side: Side
    setup: str                       # setup name from the library
    strength: float = 1.0            # 0..1, used for sizing
    entry: Optional[float] = None    # None = market at next open
    stop: Optional[float] = None
    target: Optional[float] = None
    horizon: int = 5                 # max bars to hold
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.ts, tz=timezone.utc)


@dataclass
class Order:
    """An order the portfolio submits to the broker."""
    ts: float
    symbol: str
    side: Side
    qty: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    # Bracket fields (take-profit / stop-loss).  Filled by the strategy.
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    time_in_force: str = "GTC"       # GTC, DAY, IOC
    tag: str = ""                    # setup name or strategy id
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: Optional[float] = None
    reject_reason: Optional[str] = None
    # Internal id assigned by the broker.
    order_id: Optional[int] = None

    @property
    def is_active(self) -> bool:
        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIAL)


@dataclass
class Fill:
    """A fill event from the broker."""
    ts: float
    order_id: int
    symbol: str
    side: Side
    qty: float
    price: float
    commission: float
    slippage_bps: float              # realized slippage in basis points
    tag: str = ""

    @property
    def notional(self) -> float:
        return abs(self.qty * self.price)


@dataclass
class Position:
    """An open position in the portfolio.  Long qty > 0, Short qty < 0."""
    symbol: str
    qty: float
    avg_price: float
    # Attached bracket (may be None for market-only positions).
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    # Track the setup that opened this position (for attribution).
    setup: str = ""
    opened_ts: float = 0.0
    # Max-horizon: flat the position after this many bars.
    horizon: int = 0
    bars_held: int = 0

    @property
    def is_long(self) -> bool:
        return self.qty > 0

    @property
    def is_short(self) -> bool:
        return self.qty < 0

    @property
    def is_flat(self) -> bool:
        return abs(self.qty) < 1e-9

    def market_value(self, price: float) -> float:
        """Mark-to-market value of the position (signed)."""
        return self.qty * (price - self.avg_price)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d
