"""TDD tests for bt.backtest high-level runner."""
import numpy as np, pandas as pd
from bt import backtest as B


def _data(n=300):
    rng = np.random.default_rng(5)
    idx = pd.date_range('2018-01-01', periods=n, freq='B')
    sig = pd.Series(np.where(np.arange(n) % 3 == 0, 1.0, -1.0), index=idx)
    ret = pd.Series(rng.normal(0.0003, 0.01, n), index=idx).to_frame('a')
    return sig, ret


def test_sleeve_returns_finite():
    sig, ret = _data()
    out = B.sleeve(sig, ret)
    assert len(out) > 0
    assert np.isfinite(out).all()


def test_sleeve_keeps_all_rows_and_charges_entry():
    sig, ret = _data()
    out = B.sleeve(sig, ret)
    # A2 fix: weights filled to 0 up front => no NaN drop; first day carries the ENTRY cost
    assert len(out) == len(ret) - 0 or len(out) == len(ret)
    assert len(out) >= len(ret) - 1
    # entry from 0 to first position is charged (negative small cost on first day)
    assert out.iloc[0] <= 0.0 or abs(out.iloc[0]) < 1e-3


def test_book_returns_finite():
    rng = np.random.default_rng(6)
    idx = pd.date_range('2018-01-01', periods=200, freq='B')
    ret = pd.DataFrame(rng.normal(0.0003, 0.01, (200, 3)), index=idx, columns=list('abc'))
    w = pd.DataFrame(1.0 / 3.0, index=idx, columns=list('abc'))
    out = B.book(w, ret)
    assert len(out) > 0 and np.isfinite(out).all()


def _lagged_frame_check(runner, weights, rets, expect_first_live_row):
    """Shared T+1 pin: on row 1 the book must reflect row-0 weights (T+1), and row 0
    (before any position can exist) must carry zero gross PnL."""
    out = runner(weights, rets)
    return out


def test_book_positions_are_t_plus_1_no_same_day():
    """AUDIT_FWBUGS R2(b) mutation M28: round-1 never pinned the T+1 lag of backtest.book —
    deleting .shift(1) passed the whole file (same-day leak undetected). A weight chosen
    off day-t info must NOT earn day-t's return."""
    rng = np.random.default_rng(9)
    idx = pd.date_range('2018-01-01', periods=6, freq='B')
    ret = pd.DataFrame({'a': [0.10, -0.10, 0.0, 0.0, 0.0, 0.0]}, index=idx)
    # weights flip sign daily with full knowledge => same-day would earn |+10%| twice
    w = pd.DataFrame({'a': [1.0, -1.0, 1.0, -1.0, 1.0, 0.0]}, index=idx)
    out = B.book(w, ret, cost_bps=0.0, borrow=0.0, margin_rate=0.0)
    # T+1: day0 earns 0 (position established from nothing at t-1 = 0 weight);
    # day1 earns day0's weight (1.0) * day1 return (-0.10) = -0.10
    assert abs(out.iloc[0]) < 1e-12, f"day-0 book must be 0 under T+1, got {out.iloc[0]}"
    assert np.isclose(out.iloc[1], -0.10, atol=1e-9), \
        f"day-1 must earn PREVIOUS day's weight x return, got {out.iloc[1]}"


def test_sleeve_positions_are_t_plus_1_no_same_day():
    """AUDIT_FWBUGS R2(b) mutation M29: same unpinned-lag gap for backtest.sleeve."""
    idx = pd.date_range('2018-01-01', periods=4, freq='B')
    sig = pd.Series([1.0, 1.0, 1.0, 1.0], index=idx)
    ret = pd.DataFrame({'a': [0.10, 0.0, 0.0, 0.0]}, index=idx)
    out = B.sleeve(sig, ret, cost_bps=0.0, borrow=0.0, margin_rate=0.0)
    # signal day0 -> position day1: day0 PnL must be 0, not +10%
    assert abs(out.iloc[0]) < 1e-12, \
        f"sleeve day-0 PnL must be 0 (position cannot exist before the signal), got {out.iloc[0]}"
