"""Performance metrics, aligned with ``wt.analysis._stats`` + DSR.

We reuse the same definitions the scanner uses for validating setups, so a
simulation's out-of-sample performance is directly comparable to the
per-setup gates in ``analysis.trade_qualifies``.

Key metrics:
  * per-trade Sharpe = E[R] / sd(R)
  * t-stat = sqrt(N) * E[R] / sd(R)
  * max drawdown (peak-to-trough on the equity curve)
  * Deflated Sharpe Ratio (Bailey-LdP) -- adjusts the observed Sharpe for
    the expected max of N noise trials (multiple-testing correction).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def stdev(xs: Sequence[float], ddof: int = 1) -> float:
    n = len(xs)
    if n - ddof <= 0:
        return 0.0
    m = mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (n - ddof)
    return math.sqrt(var)


def sharpe(returns: Sequence[float], periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio of a return series."""
    if len(returns) < 2:
        return 0.0
    m = mean(returns)
    sd = stdev(returns)
    if sd <= 0:
        return 0.0
    return (m / sd) * math.sqrt(periods_per_year)


def max_drawdown(equity: Sequence[float]) -> Tuple[float, int, int]:
    """Return (max_dd_fraction, peak_idx, trough_idx) for an equity curve."""
    if not equity:
        return 0.0, 0, 0
    peak = equity[0]
    peak_i = 0
    max_dd = 0.0
    max_dd_peak_i = 0
    max_dd_trough_i = 0
    for i, v in enumerate(eity := equity):
        if v > peak:
            peak = v
            peak_i = i
        if peak > 0:
            dd = (peak - v) / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_peak_i = peak_i
                max_dd_trough_i = i
    return max_dd, max_dd_peak_i, max_dd_trough_i


def deflated_sharpe(sharpe_obs: float, n_trials: int, n_obs: int,
                    skew: float = 0.0, kurt: float = 3.0) -> float:
    """Deflated Sharpe Ratio (Bailey & Lopez de Prado 2014).

    Returns the DSR statistic.  DSR < 0 means the observed Sharpe is
    consistent with the expected max of N noise trials (selection bias);
    DSR > 0 means it exceeds the selection-bias threshold.

    Parameters
    ----------
    sharpe_obs : float
        the observed (annualized) Sharpe ratio.
    n_trials : int
        number of independent trials in the multiple-testing family.
    n_obs : int
        number of observations used to estimate ``sharpe_obs``.
    skew, kurt : float
        skewness and kurtosis of the return distribution (non-normal
        correction).
    """
    if n_obs < 2 or n_trials < 1:
        return 0.0
    # Expected max of N independent Gaussian trials.
    if n_trials == 1:
        e_max = 0.0
    else:
        e_max = math.sqrt(2.0 * math.log(n_trials))
    # Variance of the estimated Sharpe (non-normal correction).
    gamma = -0.5772156649     # Euler-Mascheroni
    # Standard error of Sharpe (Lo 2002, Bailey-LdP 2014 eq. 7).
    se = math.sqrt(
        (1 - skew * sharpe_obs * math.sqrt(1.0 / n_obs)
         + (kurt - 1) / 4 * sharpe_obs ** 2 / n_obs) / n_obs
    )
    if se <= 0:
        return 0.0
    # DSR statistic (standard normal under the null of selection bias).
    dsr = (sharpe_obs - e_max) / se
    return dsr


@dataclass
class PerfStats:
    """Summary statistics for a simulation run."""
    n_trades: int = 0
    n_winners: int = 0
    n_losers: int = 0
    p_win: float = 0.0
    avg_ret: float = 0.0
    sd_ret: float = 0.0
    per_trade_sharpe: float = 0.0
    tstat: float = 0.0
    annualized_sharpe: float = 0.0
    total_return: float = 0.0
    cagr: float = 0.0
    max_drawdown: float = 0.0
    worst_trade: float = 0.0
    max_loss_streak: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    dsr: float = 0.0
    equity_curve: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        return d


def perf_stats(returns: Sequence[float], equity: Sequence[float],
               n_trials: int = 1, periods_per_year: int = 252,
               trade_returns: Optional[Sequence[float]] = None
               ) -> PerfStats:
    """Compute full performance stats for a simulation.

    ``returns`` : per-bar returns of the equity curve.
    ``equity``  : the equity curve (same length as returns, or +1).
    ``n_trials``: number of independent strategy variants tried (for DSR).
    ``trade_returns``: if provided, per-trade returns (used for win rate,
                       per-trade Sharpe, etc).  If None, derived from equity
                       differences at trade-close points.
    """
    ps = PerfStats()
    if not equity:
        return ps
    eq = list(equity)
    ps.equity_curve = eq

    # Trade-level stats.
    tr = list(trade_returns) if trade_returns is not None else \
        [eq[i] / eq[i - 1] - 1.0 for i in range(1, len(eq)) if eq[i - 1] > 0]
    if tr:
        ps.n_trades = len(tr)
        ps.n_winners = sum(1 for r in tr if r > 0)
        ps.n_losers = sum(1 for r in tr if r < 0)
        ps.p_win = ps.n_winners / ps.n_trades if ps.n_trades else 0.0
        ps.avg_ret = mean(tr)
        ps.sd_ret = stdev(tr)
        ps.per_trade_sharpe = (ps.avg_ret / ps.sd_ret) if ps.sd_ret > 0 else 0.0
        ps.tstat = (math.sqrt(ps.n_trades) * ps.avg_ret / ps.sd_ret
                    if ps.sd_ret > 0 and ps.n_trades > 0 else 0.0)
        ps.worst_trade = min(tr) if tr else 0.0
        wins = [r for r in tr if r > 0]
        losses = [r for r in tr if r < 0]
        ps.avg_win = mean(wins) if wins else 0.0
        ps.avg_loss = mean(losses) if losses else 0.0
        gross_win = sum(wins)
        gross_loss = -sum(losses)
        ps.profit_factor = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
        # Max loss streak.
        cur = 0; mx = 0
        for r in tr:
            if r < 0:
                cur += 1; mx = max(mx, cur)
            else:
                cur = 0
        ps.max_loss_streak = mx

    # Equity-curve stats.
    rets = list(returns) if returns else \
        [eq[i] / eq[i - 1] - 1.0 for i in range(1, len(eq)) if eq[i - 1] > 0]
    ps.annualized_sharpe = sharpe(rets, periods_per_year=periods_per_year)
    if len(eq) >= 2 and eq[0] > 0:
        ps.total_return = eq[-1] / eq[0] - 1.0
        years = (len(eq) - 1) / max(periods_per_year, 1)
        if years > 0:
            ps.cagr = (eq[-1] / eq[0]) ** (1.0 / years) - 1.0
    ps.max_drawdown, _, _ = max_drawdown(eq)
    # DSR uses the per-trade Sharpe (comparable to the scanner's edge).
    ps.dsr = deflated_sharpe(ps.per_trade_sharpe, n_trials, ps.n_trades)
    return ps
