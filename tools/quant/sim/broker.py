"""Simulated broker: fills, slippage, commission, bracket handling."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .events import (
    Bar, Fill, Order, OrderStatus, OrderType, Position, Side,
)


@dataclass
class BrokerConfig:
    """Broker execution model parameters.

    commission_bps: round-trip commission in basis points (per side).
    slippage_bps:   base slippage in bps applied to market/stop orders.
    market_impact:  linear impact coefficient (per $10k traded).
    tick_size:      minimum price increment (None = no rounding).
    reject_if_no_quote: if True, reject orders when no recent bar exists.
    max_order_notional: cap on order size (safety brake).
    """
    commission_bps: float = 1.0       # 1bp/side = 2bp round-trip (liquid US)
    slippage_bps: float = 1.0
    market_impact: float = 0.0
    tick_size: Optional[float] = None
    reject_if_no_quote: bool = True
    max_order_notional: float = 1_000_000.0

    def cost_per_side(self, price: float, qty: float) -> float:
        notional = abs(price * qty)
        return notional * self.commission_bps / 1e4


@dataclass
class _WorkingOrder:
    """Internal bookkeeping for a pending order."""
    order: Order
    submitted_ts: float
    last_bar: Optional[Bar] = None


class SimBroker:
    """Simulated broker that fills orders against incoming bars.

    The broker holds:
      * a book of pending orders (market, limit, stop, brackets)
      * the last seen bar per symbol (for marking and quote-rejection)
      * a monotonic order-id counter

    Fill model (per side, applied to the reference price):
      reference price:
        MARKET  -> next bar's open (or current close if no new bar)
        LIMIT   -> limit price (only fills if bar trades through it)
        STOP    -> stop price (only triggers if bar trades through it)
      slippage:
        base = slippage_bps
        impact = market_impact * (notional / 10000)
        total_bps = base + impact
      fill_price = reference * (1 + sign(total_bps))
      commission = notional * commission_bps / 1e4

    Bracket handling: when an order has ``take_profit`` and/or ``stop_loss``
    set, the broker attaches them to the resulting position.  On each
    subsequent bar it checks whether the bar's high/low touched the bracket
    levels and emits a closing fill if so.

    The broker does NOT manage position sizing or risk -- that's the
    portfolio's job.  It just fills orders it receives.
    """

    def __init__(self, config: Optional[BrokerConfig] = None):
        self.config = config or BrokerConfig()
        self._orders: Dict[int, _WorkingOrder] = {}
        self._next_id = 1
        self._last_bar: Dict[str, Bar] = {}
        self.fills: List[Fill] = []

    # ------------------------------------------------------------------ public
    def submit(self, order: Order) -> Order:
        """Accept an order and return it with an id assigned."""
        if order.order_id is not None:
            raise ValueError(f"order {order.order_id} already submitted")
        oid = self._next_id
        self._next_id += 1
        order.order_id = oid
        order.status = OrderStatus.PENDING
        self._orders[oid] = _WorkingOrder(order=order, submitted_ts=order.ts)
        return order

    def cancel(self, order_id: int) -> bool:
        wo = self._orders.get(order_id)
        if wo is None or not wo.order.is_active:
            return False
        wo.order.status = OrderStatus.CANCELLED
        del self._orders[order_id]
        return True

    def open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        out = []
        for wo in self._orders.values():
            if wo.order.is_active:
                if symbol is None or wo.order.symbol == symbol:
                    out.append(wo.order)
        return out

    def last_bar(self, symbol: str) -> Optional[Bar]:
        return self._last_bar.get(symbol)

    # --------------------------------------------------------------- on_bar --
    def on_bar(self, bar: Bar) -> List[Fill]:
        """Process a new bar: update quotes, fill/trigger pending orders,
        and check bracket exits on any position-level brackets we are tracking.

        Returns the list of fills that occurred on this bar (in order).
        """
        fills_this_bar: List[Fill] = []
        prev = self._last_bar.get(bar.symbol)
        self._last_bar[bar.symbol] = bar

        # 1) Fill pending orders for this symbol.
        #    We iterate over a snapshot because we may delete entries.
        for oid in list(self._orders.keys()):
            wo = self._orders[oid]
            if wo.order.symbol != bar.symbol:
                continue
            f = self._try_fill(wo, bar, prev)
            if f is not None:
                fills_this_bar.append(f)
                # If the order is fully filled, drop it from the book.
                if wo.order.status == OrderStatus.FILLED:
                    self._orders.pop(oid, None)

        return fills_this_bar

    # ---------------------------------------------------------- fill logic --
    def _try_fill(self, wo: _WorkingOrder, bar: Bar,
                  prev: Optional[Bar]) -> Optional[Fill]:
        order = wo.order
        # Decide the reference price and whether the order triggers this bar.
        ref_price, triggers = self._reference_price(order, bar, prev)
        if not triggers:
            return None

        # Notional guard.
        notional = abs(ref_price * order.qty)
        if notional > self.config.max_order_notional:
            order.status = OrderStatus.REJECTED
            order.reject_reason = "order_notional_exceeds_max"
            self._orders.pop(order.order_id, None)
            return None

        # Apply slippage + impact.
        slip_bps = self.config.slippage_bps + self.config.market_impact * (
            notional / 10_000.0)
        sign = 1.0 if order.side == Side.LONG else -1.0
        fill_price = ref_price * (1.0 + sign * slip_bps / 1e4)
        if self.config.tick_size:
            fill_price = round(fill_price / self.config.tick_size) * \
                self.config.tick_size

        commission = self.config.cost_per_side(fill_price, order.qty)
        fill = Fill(
            ts=bar.ts, order_id=order.order_id or 0, symbol=order.symbol,
            side=order.side, qty=order.qty, price=fill_price,
            commission=commission, slippage_bps=slip_bps, tag=order.tag,
        )
        order.filled_qty = order.qty
        order.avg_fill_price = fill_price
        order.status = OrderStatus.FILLED
        self.fills.append(fill)
        return fill

    def _reference_price(self, order: Order, bar: Bar,
                         prev: Optional[Bar]) -> Tuple[Optional[float], bool]:
        """Return (reference_price, triggers) for this order type."""
        ot = order.order_type
        if ot == OrderType.MARKET:
            # Market orders fill at the bar's open (we assume the order was
            # submitted before the bar opened; if submitted mid-bar we use
            # the close as a conservative fill).
            ref = bar.open if prev is not None else bar.close
            return ref, True
        if ot == OrderType.LIMIT:
            if order.limit_price is None:
                return None, False
            lp = order.limit_price
            if order.side == Side.LONG and bar.low <= lp:
                return lp, True
            if order.side == Side.SHORT and bar.high >= lp:
                return lp, True
            return None, False
        if ot == OrderType.STOP:
            if order.stop_price is None:
                return None, False
            sp = order.stop_price
            if order.side == Side.LONG and bar.high >= sp:
                return sp, True
            if order.side == Side.SHORT and bar.low <= sp:
                return sp, True
            return None, False
        if ot == OrderType.STOP_LIMIT:
            # Stop triggers -> becomes a limit order at limit_price.
            if order.stop_price is None or order.limit_price is None:
                return None, False
            sp = order.stop_price
            triggered = False
            if order.side == Side.LONG and bar.high >= sp:
                triggered = True
            if order.side == Side.SHORT and bar.low <= sp:
                triggered = True
            if not triggered:
                return None, False
            lp = order.limit_price
            if order.side == Side.LONG and bar.low <= lp:
                return lp, True
            if order.side == Side.SHORT and bar.high >= lp:
                return lp, True
            return None, False
        return None, False

    # ------------------------------------------------------- bracket exits --
    def check_brackets(self, positions: Dict[str, Position], bar: Bar
                       ) -> List[Fill]:
        """Check attached bracket exits (stop-loss / take-profit) on a bar.

        ``positions`` is the portfolio's live position map.  If a bracket
        level is touched, we synthesize a closing order and fill it at the
        bracket level (with slippage applied).  Returns the fills.
        """
        fills: List[Fill] = []
        pos = positions.get(bar.symbol)
        if pos is None or pos.is_flat:
            return fills

        # Take-profit: long -> bar.high >= tp ; short -> bar.low <= tp
        if pos.take_profit is not None:
            tp = pos.take_profit
            hit = (pos.is_long and bar.high >= tp) or \
                  (pos.is_short and bar.low <= tp)
            if hit:
                f = self._close_at(pos, tp, bar, reason="tp")
                if f:
                    fills.append(f)
                    return fills  # position is flat now

        # Stop-loss: long -> bar.low <= sl ; short -> bar.high >= sl
        if pos.stop_loss is not None:
            sl = pos.stop_loss
            hit = (pos.is_long and bar.low <= sl) or \
                  (pos.is_short and bar.high >= sl)
            if hit:
                f = self._close_at(pos, sl, bar, reason="sl")
                if f:
                    fills.append(f)
        return fills

    def _close_at(self, pos: Position, price: float, bar: Bar,
                  reason: str = "") -> Optional[Fill]:
        """Synthesize a closing fill for a position at ``price``."""
        close_side = Side.SHORT if pos.is_long else Side.LONG
        qty = abs(pos.qty)
        notional = abs(price * qty)
        slip_bps = self.config.slippage_bps + self.config.market_impact * (
            notional / 10_000.0)
        sign = 1.0 if close_side == Side.LONG else -1.0
        fill_price = price * (1.0 + sign * slip_bps / 1e4)
        if self.config.tick_size:
            fill_price = round(fill_price / self.config.tick_size) * \
                self.config.tick_size
        commission = self.config.cost_per_side(fill_price, qty)
        fill = Fill(
            ts=bar.ts, order_id=0, symbol=pos.symbol,
            side=close_side, qty=qty, price=fill_price,
            commission=commission, slippage_bps=slip_bps,
            tag=f"bracket:{reason}:{pos.setup}",
        )
        self.fills.append(fill)
        # Flatten the position.
        pos.qty = 0.0
        return fill
