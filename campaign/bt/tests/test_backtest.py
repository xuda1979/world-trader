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


def test_sleeve_drops_first_nan_day():
    sig, ret = _data()
    out = B.sleeve(sig, ret)
    # the first day's position is NaN (no prior signal) and is dropped by dropna()
    assert len(out) == len(ret) - 1


def test_book_returns_finite():
    rng = np.random.default_rng(6)
    idx = pd.date_range('2018-01-01', periods=200, freq='B')
    ret = pd.DataFrame(rng.normal(0.0003, 0.01, (200, 3)), index=idx, columns=list('abc'))
    w = pd.DataFrame(1.0 / 3.0, index=idx, columns=list('abc'))
    out = B.book(w, ret)
    assert len(out) > 0 and np.isfinite(out).all()
