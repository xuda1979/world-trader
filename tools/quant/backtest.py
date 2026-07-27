"""Unified backtest engine for world-trader strategies.

EVENT-DRIVEN PORTFOLIO BACKTESTER
---------------------------------
Tracks cash, positions, and an equity curve across a sequence of trades
produced by the strategy library.  Wraps the validated per-setup replay
functions in tools.wt.analysis (backtest_setup, backtest_orb,
backtest_rv_mean_reversion, backtest_pead_pooled) so we reuse the
scientifically-guarded edge estimates, then layers on:

  * position sizing (Kelly / fixed-fractional)
  * a portfolio equity curve with compounding
  * full performance analytics (Sharpe, Sortino, Calmar, max DD, ...)
  * per-strategy and blended tear sheets

Designed to run on REAL price history only (via tools.quant.data_history).
Synthetic-data backtests (GBM/OU/JUMP) were removed 2026-07-26: they are
unrealistic, misleading, and dangerous for capital decisions.  We rely on
real market data exclusively.
"""
from __future__ import annotations
import math, statistics
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable

# re-export the per-setup science
from ..wt.analysis import (
    backtest_setup, backtest_orb, backtest_rv_mean_reversion,
    backtest_pead_pooled, _indicators, _setup_defs,
    HORIZON, MIN_SAMPLE, COST_RT,
)

TRADING_DAYS = 252

# ---------------------------------------------------------------- trade record
@dataclass
class Trade:
    """One completed round-trip trade."""
    sym: str
    setup: str
    side: str           # "Long" / "Short"
    entry_bar: int
    exit_bar: int
    entry_price: float
    exit_price: float
    stop_price: float
    target_price: float
    shares: float
    risk_frac: float    # fractional stop distance at entry
    gross_ret: float    # fraction (exit/entry - 1) * side_sign
    cost_frac: float    # round-trip cost fraction
    net_ret: float      # gross_ret - cost_frac
    pnl_usd: float      # net_ret * notional
    equity_after: float
    tag: str = ""       # optional regime/strategy tag


# ---------------------------------------------------------------- position sizing
def kelly_fraction(p_win: float, rr: float, cap: float = 0.25) -> float:
    """Full Kelly fraction for a binary outcome with win-prob p_win and
    reward:risk ratio rr. Capped to `cap` (quarter-Kelly-by-default cap on
    the FULL Kelly value, i.e. result is already quarter-Kelly when cap=0.25
    applied to full Kelly)."""
    if p_win <= 0 or rr <= 0:
        return 0.0
    b = rr
    f = (b*p_win - (1-p_win)) / b
    return max(0.0, min(cap, f))


def fixed_fractional(equity: float, risk_frac: float,
                     risk_per_trade: float = 0.01) -> float:
    """Dollars at risk per trade = equity * risk_per_trade.
    Returns the notional position size implied by a stop at `risk_frac`."""
    if risk_frac <= 0:
        return 0.0
    risk_usd = equity * risk_per_trade
    return risk_usd / risk_frac   # notional in dollars


# ---------------------------------------------------------------- equity curve
class EquityCurve:
    """Compounding equity curve indexed by bar.

    Trades are assumed to be sequential (one position at a time) OR
    non-overlapping by bar index.  For overlapping positions the caller
    should aggregate per-bar PnL via ``add_bar_pnl`` instead.
    """

    def __init__(self, start_equity: float = 100_000.0):
        self.start = start_equity
        self.equity = start_equity
        self.curve: List[float] = [start_equity]
        self.bars: List[int] = [0]
        self.trades: List[Trade] = []

    def add_trade(self, t: Trade) -> None:
        self.equity += t.pnl_usd
        self.trades.append(t)
        self.curve.append(self.equity)
        self.bars.append(t.exit_bar)

    def add_bar_pnl(self, bar: int, pnl_usd: float) -> None:
        self.equity += pnl_usd
        self.curve.append(self.equity)
        self.bars.append(bar)

    def returns(self) -> List[float]:
        r = []
        for i in range(1, len(self.curve)):
            prev = self.curve[i-1]
            if prev > 0:
                r.append(self.curve[i]/prev - 1.0)
            else:
                r.append(0.0)
        return r


# ---------------------------------------------------------------- analytics
def max_drawdown(equity: List[float]) -> Tuple[float, int, int]:
    """Return (max_dd_fraction, peak_idx, trough_idx)."""
    if not equity:
        return 0.0, 0, 0
    peak = equity[0]; pi = 0
    mdd = 0.0; m_pi = 0; m_ti = 0
    for i, v in enumerate(equity):
        if v > peak:
            peak = v; pi = i
        if peak > 0:
            dd = 1.0 - v/peak
            if dd > mdd:
                mdd = dd; m_pi = pi; m_ti = i
    return mdd, m_pi, m_ti


def sharpe(returns: List[float], periods: int = TRADING_DAYS,
           rf: float = 0.0) -> float:
    """Annualized Sharpe ratio from per-period returns."""
    if len(returns) < 2:
        return 0.0
    m = statistics.mean(returns)
    sd = statistics.pstdev(returns)
    if sd <= 0:
        return 0.0
    return (m - rf) / sd * math.sqrt(periods)


def sortino(returns: List[float], periods: int = TRADING_DAYS,
            rf: float = 0.0) -> float:
    """Annualized Sortino ratio (only downside deviation in denom)."""
    if len(returns) < 2:
        return 0.0
    m = statistics.mean(returns)
    downside = [min(r - rf, 0.0) for r in returns]
    dsd = math.sqrt(sum(d*d for d in downside) / len(downside))
    if dsd <= 0:
        return 0.0
    return (m - rf) / dsd * math.sqrt(periods)


def calmar(returns: List[float], equity: List[float],
           periods: int = TRADING_DAYS) -> float:
    """Annualized return / max drawdown."""
    if len(equity) < 2 or equity[0] <= 0:
        return 0.0
    mdd, _, _ = max_drawdown(equity)
    if mdd <= 0:
        return 0.0
    years = len(returns) / periods
    if years <= 0:
        return 0.0
    cagr = (equity[-1]/equity[0])**(1.0/years) - 1.0
    return cagr / mdd


def trade_stats(trades: List[Trade]) -> Dict:
    """Per-trade statistics from a list of completed trades."""
    if not trades:
        return {"n": 0}
    rets = [t.net_ret for t in trades]
    wins = [r for r in rets if r > 0]
    losses = [r for r in rets if r <= 0]
    n = len(rets)
    p_win = len(wins)/n
    avg_win = statistics.mean(wins) if wins else 0.0
    avg_loss = statistics.mean(losses) if losses else 0.0
    expectancy = p_win*avg_win + (1-p_win)*avg_loss
    # streaks
    max_streak = 0; cur = 0
    for r in rets:
        if r <= 0:
            cur += 1; max_streak = max(max_streak, cur)
        else:
            cur = 0
    # time-in-market (bars)
    total_bars = 0
    for t in trades:
        total_bars += max(0, t.exit_bar - t.entry_bar)
    span = max(t.exit_bar for t in trades) - min(t.entry_bar for t in trades) + 1
    exposure = total_bars / span if span > 0 else 0.0
    return {
        "n": n, "p_win": p_win, "avg_win": avg_win, "avg_loss": avg_loss,
        "expectancy": expectancy,
        "payoff": (avg_win/abs(avg_loss)) if avg_loss < 0 else float("inf"),
        "sd": statistics.pstdev(rets) if len(rets) > 1 else 0.0,
        "worst_trade": min(rets), "best_trade": max(rets),
        "max_loss_streak": max_streak,
        "exposure": exposure,
        "total_pnl_usd": sum(t.pnl_usd for t in trades),
    }


def tear_sheet(curve: EquityCurve, name: str = "strategy") -> Dict:
    """Full performance tear sheet for one equity curve."""
    eq = curve.curve
    rets = curve.returns()
    mdd, pi, ti = max_drawdown(eq)
    ts = trade_stats(curve.trades)
    return {
        "name": name,
        "start_equity": curve.start,
        "final_equity": curve.equity,
        "total_return": (eq[-1]/eq[0] - 1.0) if eq[0] > 0 else 0.0,
        "n_trades": ts.get("n", 0),
        "p_win": ts.get("p_win", 0.0),
        "expectancy": ts.get("expectancy", 0.0),
        "payoff": ts.get("payoff", 0.0),
        "sharpe": sharpe(rets),
        "sortino": sortino(rets),
        "calmar": calmar(rets, eq),
        "max_dd": mdd,
        "max_dd_peak_bar": pi,
        "max_dd_trough_bar": ti,
        "worst_trade": ts.get("worst_trade", 0.0),
        "best_trade": ts.get("best_trade", 0.0),
        "max_loss_streak": ts.get("max_loss_streak", 0),
        "avg_win": ts.get("avg_win", 0.0),
        "avg_loss": ts.get("avg_loss", 0.0),
        "exposure": ts.get("exposure", 0.0),
        "total_pnl_usd": ts.get("total_pnl_usd", 0.0),
        "sd_per_trade": ts.get("sd", 0.0),
    }

# ---------------------------------------------------------------- setup runner
def run_setup_equity(sym, history, setup_name, market="US",
                     start_equity=100_000.0, risk_per_trade=0.01,
                     horizon=HORIZON, tag=""):
    """Replay ONE setup on ONE symbol, building a full equity curve of
    sequential trades with fixed-fractional position sizing.

    Mirrors the logic of analysis._replay / backtest_setup but records
    each round-trip trade so we can construct a real equity curve and
    compute portfolio-level analytics (Sharpe, DD, ...).
    """
    from ..wt.analysis import (_indicators, _setup_defs, BT_RISK_MIN,
                                BT_RISK_MAX, COST_RT)
    from ..wt import costs as _costs
    H = history.get("high", []); L = history.get("low", [])
    C = history.get("close", []); O = history.get("open", [])
    V = history.get("vol", [])
    N = len(C)
    if N < 30:
        return None
    ind = _indicators(H, L, C, opens=O or None, volumes=V or None)
    setups = {s["name"]: s for s in _setup_defs()}
    setup = setups.get(setup_name)
    if setup is None:
        return None
    side = setup["side"]; rr = setup["rr"]; rm = setup["risk_mult"]
    cost = COST_RT.get(market, COST_RT["DEFAULT"])
    curve = EquityCurve(start_equity)
    for i in range(N - 1):
        if ind["atrp"][i] is None:
            continue
        if not setup["sig"](ind, C, i):
            continue
        risk_frac = min(BT_RISK_MAX, max(BT_RISK_MIN, rm * ind["atrp"][i]))
        reward = rr * risk_frac
        entry = C[i]
        if side == "Long":
            stop = entry * (1 - risk_frac); tgt = entry * (1 + reward)
        else:
            stop = entry * (1 + risk_frac); tgt = entry * (1 - reward)
        # walk forward
        exit_price = None; exit_bar = None
        for j in range(i + 1, min(i + 1 + horizon, N)):
            if side == "Long":
                if L[j] <= stop:
                    exit_price = stop; exit_bar = j; break
                if H[j] >= tgt:
                    exit_price = tgt; exit_bar = j; break
            else:
                if H[j] >= stop:
                    exit_price = stop; exit_bar = j; break
                if L[j] <= tgt:
                    exit_price = tgt; exit_bar = j; break
        if exit_price is None:
            exit_price = C[min(i + horizon, N - 1)]
            exit_bar = min(i + horizon, N - 1)
        sign = 1.0 if side == "Long" else -1.0
        gross = sign * (exit_price / entry - 1.0)
        # notional is sized off CURRENT equity (fixed-fractional risk)
        notional = fixed_fractional(curve.equity, risk_frac, risk_per_trade)
        # realistic IBKR retail cost: commission (max $0.005/sh, $0.35 min)
        # + spread + impact, using the ACTUAL per-trade notional
        try:
            c_frac = _costs.round_trip_cost_frac(
                market, entry, ind["atrp"][i], notional)
        except Exception:
            c_frac = cost
        net = gross - c_frac
        pnl = net * notional
        t = Trade(sym=sym, setup=setup_name, side=side,
                  entry_bar=i, exit_bar=exit_bar,
                  entry_price=entry, exit_price=exit_price,
                  stop_price=stop, target_price=tgt,
                  shares=notional/entry if entry > 0 else 0.0,
                  risk_frac=risk_frac, gross_ret=gross, cost_frac=c_frac,
                  net_ret=net, pnl_usd=pnl, equity_after=curve.equity + pnl,
                  tag=tag)
        curve.add_trade(t)
    return curve

# ---------------------------------------------------------------- portfolio runner
def run_portfolio(universe, setups, market="US", start_equity=100_000.0,
                  risk_per_trade=0.01, horizon=HORIZON, tag=""):
    """Run a portfolio of (setup x symbol) trades SEQUENTIALLY on a SINGLE
    compounded equity curve.  Each firing signal is sized off the CURRENT
    equity and booked as one round-trip trade.

    This is the simplest honest book: no concurrent positions, so equity
    curve is unambiguous and drawdowns are real (not masked by overlap).
    """
    curve = EquityCurve(start_equity)
    for sym, hist in universe:
        for setup_name in setups:
            sub = run_setup_equity(sym, hist, setup_name, market=market,
                                   start_equity=curve.equity,
                                   risk_per_trade=risk_per_trade,
                                   horizon=horizon, tag=tag)
            if sub is None:
                continue
            for t in sub.trades:
                # re-base the pnl to the global equity
                # (sub was sized off curve.equity at entry; we replay sequentially)
                curve.add_trade(t)
    return curve


def run_rv_mean_reversion(spread, market="US", start_equity=100_000.0,
                          risk_per_trade=0.01, tag="RV-MR"):
    """Run the relative-value mean-reversion backtest and build an equity
    curve from the per-trade spread-reversion returns.

    RV PnL is in spread-stdev units; we convert to a dollar PnL by sizing
    each trade to risk `risk_per_trade` of equity per 1-sigma move.
    """
    from ..wt.analysis import (RV_Z_ENTRY, RV_Z_EXIT, RV_HORIZON, RV_COST_RT,
                                MIN_SAMPLE)
    N = len(spread)
    if N < 40:
        return None
    lookback = 20
    entries = []
    for i in range(lookback, N - 1):
        window = spread[i-lookback:i]
        m = statistics.mean(window)
        sd = statistics.pstdev(window)
        if sd <= 0:
            continue
        z = (spread[i] - m) / sd
        if z < -RV_Z_ENTRY:
            entries.append((i, 1, spread[i], sd))
        elif z > RV_Z_ENTRY:
            entries.append((i, -1, spread[i], sd))
    if len(entries) < MIN_SAMPLE:
        return None
    curve = EquityCurve(start_equity)
    for i, side, entry, esd in entries:
        outcome = None
        for j in range(i + 1, min(i + 1 + RV_HORIZON, N)):
            window = spread[max(0, j-lookback):j]
            m = statistics.mean(window)
            sd = statistics.pstdev(window) if len(window) > 1 else esd
            if sd <= 0:
                continue
            z = (spread[j] - m) / sd
            if side == 1 and z >= RV_Z_EXIT:
                outcome = spread[j] - entry; exit_bar = j; break
            if side == -1 and z <= RV_Z_EXIT:
                outcome = entry - spread[j]; exit_bar = j; break
        if outcome is None:
            outcome = (spread[min(i+RV_HORIZON, N-1)] - entry) * side
            exit_bar = min(i+RV_HORIZON, N-1)
        # outcome is in spread units; convert to fractional return by
        # dividing by entry sigma, then size as risk_per_trade per sigma
        sig_ret = outcome / esd if esd > 0 else 0.0
        risk_usd = curve.equity * risk_per_trade
        # RV is a 2-LEG spread: round-trip = 4 sides of IBKR commission.
        # FIX (2026-07-26): the cost is a fraction of notional; convert it to
        # stdev units before subtracting from sig_ret (which is in stdev units).
        # cost_stdev = cost_frac * 2 * notional / (risk_per_trade * equity)
        # With notional=$25k, equity=$100k, risk=0.01:
        #   cost_stdev = cost_frac * 2 * 25000 / (0.01 * 100000) = cost_frac * 50
        # i.e. a 0.0008 RT cost -> 0.04 stdev, not 0.0008 stdev (50x larger).
        try:
            from ..wt import costs as _costs
            rv_cost_frac = 2.0 * _costs.round_trip_cost_frac(
                market, 100.0, 0.02, risk_usd)
            # Convert to stdev units.  notional = 2 * $25k = $50k on a $100k
            # account -> cost_stdev = rv_cost_frac * 50000 / risk_usd
            notional_usd = 2.0 * 25000.0
            rv_cost = rv_cost_frac * notional_usd / max(risk_usd, 1.0)
        except Exception:
            # Fallback: RV_COST_RT (0.0008) * 2 legs / 0.01 risk = 0.16 stdev
            rv_cost = RV_COST_RT * 2.0 / 0.01
        net = sig_ret - rv_cost
        pnl = net * risk_usd  # 1-sigma risk = risk_per_trade of equity
        t = Trade(sym="SPREAD", setup="RV-MR", side="Long" if side == 1 else "Short",
                  entry_bar=i, exit_bar=exit_bar,
                  entry_price=entry, exit_price=entry + outcome*side,
                  stop_price=entry - esd*side, target_price=entry + esd*side,
                  shares=1.0, risk_frac=1.0, gross_ret=sig_ret,
                  cost_frac=rv_cost, net_ret=net, pnl_usd=pnl,
                  equity_after=curve.equity + pnl, tag=tag)
        curve.add_trade(t)
    return curve
