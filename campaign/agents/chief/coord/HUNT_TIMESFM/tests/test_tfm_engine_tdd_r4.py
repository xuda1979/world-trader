"""ROUND 4 TDD tests for the TimesFM sleeve engine (semantics per bt/engine.py:
position decided at close t earns r[t+1] -> day 0 flat; entry turnover charged on the
first day the held weight becomes nonzero)."""
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")

import tfm_engine_r4 as eng
from bt import gates as btgates


def _toy(n=800, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-02", periods=n)
    r = pd.Series(rng.normal(0, 0.01, n), index=idx)
    return idx, r


def test_t1_positions_are_lagged():
    idx, r = _toy()
    pos = pd.Series(np.where(r > 0, 1.0, -1.0), index=idx)  # would leak if unshifted
    net = eng.sleeve_net(pos, {None: r}, vt="off")
    held = pos.shift(1).fillna(0.0)
    to = held.diff().abs()
    to.iloc[0] = abs(held.iloc[0])          # day-1 establishment if held[0] != 0
    gross = net + to * 6.4e-4 + (-held.clip(upper=0)) * 0.005 / 252
    np.testing.assert_allclose(gross.values, (held * r).values, atol=1e-12)


def test_t2_entry_day_charged():
    idx, r = _toy(50)
    pos = pd.Series(1.0, index=idx)
    net = eng.sleeve_net(pos, {None: r}, vt="off")
    # day 0 flat (T+1); day 1 is entry: turnover |1-0|=1.0 -> 6.4bps, gross = r[1]
    assert net.iloc[0] == 0.0
    assert abs(net.iloc[1] - (r.iloc[1] - 6.4e-4)) < 1e-15
    # day 2+: no turnover, no borrow -> gross only
    assert abs(net.iloc[2] - r.iloc[2]) < 1e-15


def test_t3_borrow_and_margin():
    idx, r = _toy(50)
    pos = pd.Series(-1.5, index=idx)  # short 1.5 held from day 1 -> margin on 0.5
    net = eng.sleeve_net(pos, {None: r}, vt="off")
    base = -1.5 * r - 1.5 * 0.005 / 252 - 0.5 * 0.045 / 252
    assert abs(net.iloc[1] - (base.iloc[1] - 1.5 * 6.4e-4)) < 1e-15   # entry day
    np.testing.assert_allclose(net.iloc[2:].values, base.iloc[2:].values, atol=1e-15)


def test_t4_voltarget_trailing_only():
    idx, r = _toy(300)
    s = eng.vt_scale(r, target=0.10, minlen=60, cap=3.0)
    r2 = r.copy(); r2.iloc[200:] *= 10
    s2 = eng.vt_scale(r2, target=0.10, minlen=60, cap=3.0)
    np.testing.assert_allclose(s.iloc[:200].values, s2.iloc[:200].values)
    assert float(s.max()) <= 3.0 + 1e-12


def test_t5_scramble_nan_failclosed():
    r = np.array([0.01, np.nan, 0.02])
    p, _ = btgates.scramble_positions(np.ones(3), r)
    assert not np.isfinite(p)


def test_t6_no_silent_fill():
    idx, r = _toy(60)
    r_nan = r.copy(); r_nan.iloc[30] = np.nan
    pos = pd.Series(1.0, index=idx)
    with pytest.raises(ValueError):
        eng.sleeve_net(pos, {None: r_nan}, vt="off")
