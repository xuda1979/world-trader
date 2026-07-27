"""Portfolio tracker: cash, positions, mark-to-market equity.

The portfolio is responsible for:
  * turning Signals into Orders (position sizing)
  * applying fills to positions (avg-price tracking, commission)
  * marking positions to market on each bar
  * enforcing risk limits (max position size, max leverage, max drawdown)

It does NOT decide WHEN to trade -- that's the strategy's job.  It only
sizes and risk-manages the signals it receives.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .events import Fill, Order, OrderStatus, OrderType, Position, Side, Signal


@dataclass
class PortfolioConfig:
    """Portfolio risk parameters."""
    starting_cash: float = 100_000.0
    max_position_pct: float = 0.10       # max 10% of equity per name
    max_leverage: float = 1.0            # no leverage by default
    max_positions: int = 10              # max concurrent names
    risk_per_trade_pct: float = 0.01     # risk 1% of equity per trade
    max_drawdown_pct: float = 0.25       # halt new entries at -25% from HWM
    allow_short: bool = True


@dataclass
class Portfolio:
    """Cash + positions + equity tracker.

    Equity is mark-to-market: cash + sum(position_qty * current_price).
    """
    config: PortfolioConfig = field(default_factory=PortfolioConfig)
    cash: float = 0.0
    positions: Dict[str, Position] = field(default_factory=dict)
    equity_curve: List[tuple] = field(default_factory=list)  # (ts, equity)
    realized_pnl: float = 0.0
    high_water_mark: float = 0.0

    def __post_init__(self):
        if self.cash == 0.0:
            self.cash = self.config.starting_cash
        self.high_water_mark = self.cash

    # --------------------------------------------------------- mark-to-mkt
    def mark(self, prices: Dict[str, float], ts: float) -> float:
        """Update equity with current prices; return current equity."""
        equity = self.cash
        for sym, pos in self.positions.items():
            if pos.is_flat:
                continue
            px = prices.get(sym)
            if px is None:
                px = pos.avg_price  # fallback: no mark available
            equity += pos.qty * px
        self.equity_curve.append((ts, equity))
        if equity > self.high_water_mark:
            self.high_water_mark = equity
        return equity

    def equity(self, prices: Dict[str, float]) -> float:
        eq = self.cash
        for sym, pos in self.positions.items():
            if pos.is_flat:
                continue
            px = prices.get(sym, pos.avg_price)
            eq += pos.qty * px
        return eq

    # --------------------------------------------------------- sizing ----
    def size_for_signal(self, sig: Signal, equity: float,
                        last_price: float) -> Optional[float]:
        """Position size in shares/units for a signal.

        Uses risk-based sizing: size = (risk_$) / (entry - stop).
        Falls back to ``max_position_pct`` of equity if no stop is set.
        Respects ``max_position_pct`` cap and ``max_leverage``.
        """
        if equity <= 0:
            return None
        # Drawdown brake.
        dd = (self.high_water_mark - equity) / self.high_water_mark \
            if self.high_water_mark > 0 else 0.0
        if dd >= self.config.max_drawdown_pct:
            return None
        # Max concurrent positions.
        open_n = sum(1 for p in self.positions.values() if not p.is_flat)
        if open_n >= self.config.max_positions:
            return None
        if sig.side == Side.SHORT and not self.config.allow_short:
            return None

        risk_dollars = equity * self.config.risk_per_trade_pct
        entry = sig.entry if sig.entry is not None else last_price
        stop = sig.stop
        if stop is not None and abs(entry - stop) > 1e-9:
            per_share_risk = abs(entry - stop)
            qty = risk_dollars / per_share_risk
        else:
            # No stop -> fall back to %-of-equity sizing.
            qty = (equity * self.config.max_position_pct) / entry

        # Cap by max_position_pct of equity.
        max_notional = equity * self.config.max_position_pct * self.config.max_leverage
        notional = qty * entry
        if notional > max_notional:
            qty = max_notional / entry
        return qty if qty > 0 else None

    def build_order(self, sig: Signal, qty: float, ts: float) -> Order:
        """Build an Order from a Signal + size."""
        ot = OrderType.MARKET
        limit = None
        if sig.entry is not None:
            # Use a limit order at the entry level (the strategy's
            # intended entry price).
            ot = OrderType.LIMIT
            limit = sig.entry
        return Order(
            ts=ts, symbol=sig.symbol, side=sig.side, qty=qty,
            order_type=ot, limit_price=limit,
            stop_price=None,
            take_profit=sig.target, stop_loss=sig.stop,
            tag=sig.setup,
        )

    # --------------------------------------------------------- fills -----
    def apply_fill(self, fill: Fill) -> None:
        """Update cash + positions for a fill."""
        sign = 1.0 if fill.side == Side.LONG else -1.0
        # Cash decreases by notional + commission on a buy; increases on sell.
        cost = fill.qty * fill.price * sign - fill.commission
        self.cash -= cost

        pos = self.positions.get(fill.symbol)
        if pos is None:
            pos = Position(symbol=fill.symbol, qty=0.0, avg_price=0.0,
                           setup=fill.tag, opened_ts=fill.ts)
            self.positions[fill.symbol] = pos

        new_qty = pos.qty + sign * fill.qty
        if abs(new_qty) < 1e-9:
            # Closing the position: realize P&L.
            realized = (fill.price - pos.avg_price) * pos.qty * (1 if pos.is_long else -1)
            self.realized_pnl += realized - fill.commission
            pos.qty = 0.0
            pos.avg_price = 0.0
            pos.stop_loss = None
            pos.take_profit = None
        elif (pos.qty == 0.0) or (pos.is_long and sign > 0) or (pos.is_short and sign < 0):
            # Opening or adding in the same direction: update avg price.
            total_cost = pos.avg_price * abs(pos.qty) + fill.price * fill.qty
            pos.avg_price = total_cost / abs(new_qty)
            pos.qty = new_qty
        else:
            # Reducing / closing part of the position.
            realized = (fill.price - pos.avg_price) * min(abs(pos.qty), fill.qty) * (1 if pos.is_long else -1)
            self.realized_pnl += realized - fill.commission
            pos.qty = new_qty
            if pos.is_flat:
                pos.avg_price = 0.0
                pos.stop_loss = None
                pos.take_profit = None

    def attach_bracket_to_position(self, symbol: str, stop: Optional[float],
                                    target: Optional[float]) -> None:
        """Attach a bracket (stop-loss / take-profit) to an existing position."""
        pos = self.positions.get(symbol)
        if pos is None or pos.is_flat:
            return
        pos.stop_loss = stop
        pos.take_profit = target

    def tick_horizons(self) -> List[str]:
        """Advance bars-held on all open positions; returns symbols that hit
        their max-horizon (the runner should flat them on the next bar)."""
        expired = []
        for sym, pos in list(self.positions.items()):
            if pos.is_flat:
                continue
            pos.bars_held += 1
            if pos.horizon > 0 and pos.bars_held >= pos.horizon:
                expired.append(sym)
        return expired

    def flat(self, symbol: str) -> bool:
        return self.positions.get(symbol) is None or \
            self.positions[symbol].is_flat

    def open_positions_count(self) -> int:
        return sum(1 for p in self.positions.values() if not p.is_flat)
