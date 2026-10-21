"""CAMP_BORROW: call-rate margin + borrow-tier arithmetic on a weights stream.

All short + testable + honest. Margin is charged daily on max(gross-1, 0) — the
capital-real IBKR margin-loan convention — and gross exactness is a fail-closed flag
(any day off target by >1e-9 = re-emit regression)."""
from __future__ import annotations
import numpy as np
import pandas as pd

ANN = 252.0
GROSS_TOL = 1e-9


def margin_daily(gross: pd.Series, rate: float) -> pd.Series:
    """Daily margin drag = max(gross-1, 0) * rate / 252 (fraction of NAV per day)."""
    return np.maximum(pd.Series(gross) - 1.0, 0.0) * rate / ANN


def margin_ann(gross: pd.Series, rate: float) -> float:
    """Annualized (arithmetic) margin drag in fraction/yr on a constant-gross book."""
    return float(margin_daily(gross, rate).mean() * ANN)


def gross_exact(gross: pd.Series, target: float = 1.6, tol: float = GROSS_TOL) -> tuple:
    """Fail-closed gross check. Returns (ok, max|gross-target|, n_days_beyond_tol)."""
    g = pd.Series(gross)
    dev = (g - target).abs()
    bad = int((dev > tol).sum())
    return bool(bad == 0), float(dev.max()), bad


def borrow_tier_uplift(short_notional: float, base_rate: float, tier_rate: float) -> float:
    """Extra annual borrow cost (fraction of NAV) when a short leg tiers up from base to tier."""
    return max(short_notional, 0.0) * (tier_rate - base_rate)


# ---------- round 3: call-rate PATH scenarios (time-varying financing) ----------

def rate_path(index: pd.DatetimeIndex, base: float, spikes: dict | None = None) -> pd.Series:
    """Call-rate path: constant `base` on `index`, optionally spiked over date windows.

    `spikes` maps {start_date_str: (rate, n_trading_days)}; the window covers exactly
    n_trading_days of TRADING days starting on the first index day >= start_date_str."""
    r = pd.Series(float(base), index=pd.DatetimeIndex(index))
    for start, (spike_rate, n_days) in (spikes or {}).items():
        m = spike_window(r.index, start, n_days)
        r[m] = float(spike_rate)
    return r


def spike_window(index: pd.DatetimeIndex, start: str, n_trading_days: int) -> pd.Series:
    """Boolean mask over exactly the first `n_trading_days` index days >= `start`."""
    idx = pd.DatetimeIndex(index)
    ts = pd.Timestamp(start)
    if ts < idx[0]:
        # fail-closed (R4): a start before the series begins would silently anchor at
        # idx[0], and the reported window_start would then be a lie about placement.
        raise ValueError(f"spike_window: start {start} before index begins {idx[0].date()}")
    pos = idx.searchsorted(ts)
    if pos >= len(idx):
        raise ValueError(f"spike_window: start {start} after index end {idx[-1].date()}")
    end = min(pos + int(n_trading_days), len(idx))
    if end - pos < int(n_trading_days):
        raise ValueError(f"spike_window: only {end - pos} trading days remain from {start}, "
                         f"need {n_trading_days}")
    m = pd.Series(False, index=idx)
    m.iloc[pos:end] = True
    return m


def margin_daily_path(gross: pd.Series, rate_path_s: pd.Series) -> pd.Series:
    """Daily margin drag on max(gross-1, 0) at a TIME-VARYING call rate (elementwise —
    never the time-average rate). Reduces exactly to margin_daily for a constant path."""
    g, r = pd.Series(gross), pd.Series(rate_path_s)
    if not g.index.equals(r.index):
        raise ValueError("margin_daily_path: gross and rate_path indexes must align")
    return np.maximum(g - 1.0, 0.0) * r.values / ANN


def scenario_net(port: pd.Series, turnover: pd.Series, gross: pd.Series,
                 rate: pd.Series, bps: float) -> pd.Series:
    """Path-stressed net: port - full|dW|*bps - max(gross-1,0)*r_t/252 (elementwise).
    Identical algebra to the champion builder with the scalar RATE replaced by a path."""
    port, to, g = pd.Series(port), pd.Series(turnover), pd.Series(gross)
    if not (port.index.equals(to.index) and port.index.equals(g.index)
            and port.index.equals(pd.Series(rate).index)):
        raise ValueError("scenario_net: all inputs must share one index")
    return port - to * bps / 1e4 - margin_daily_path(g, rate)


def path_metrics(r: pd.Series) -> dict:
    """ann_geo / SR_d / MDD / neg_years / worst-year for a scenario net (goal-gate fields)."""
    from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
    r = pd.Series(r).dropna()
    neg, worst = neg_years(r)
    return {"ann": ann_geo(r), "sr_d": sharpe_d(r), "mdd": max_dd(r),
            "neg_years": neg, "worst_year": worst}
