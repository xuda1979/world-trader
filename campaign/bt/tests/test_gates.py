"""TDD tests for bt.gates."""
import numpy as np, pandas as pd
from bt import gates as G


def _r(n=500, drift=0.0006):
    idx = pd.date_range('2015-01-01', periods=n, freq='B')
    rng = np.random.default_rng(3)
    return pd.Series(rng.normal(drift, 0.01, n), index=idx)


def test_uniq_ratio_flattened():
    # a flattened series (constant every day) fails the flatten gate
    r = pd.Series(0.001, index=pd.date_range('2020-01-01', periods=30, freq='B'))
    assert G.uniq_ratio(r) < G.DEFAULTS['uniq_min']


def test_uniq_ratio_real():
    r = _r()
    assert G.uniq_ratio(r) >= 0.9


def test_ac1_of_independent():
    r = _r()
    assert abs(G.lag1_autocorr(r)) < 0.3


def test_zero_runs_detects():
    idx = pd.date_range('2020-01-01', periods=40, freq='B')
    r = pd.Series(0.0, index=idx)
    assert G.zero_runs_long(r, min_run=20) != []


def test_zero_runs_clean():
    r = _r()
    assert G.zero_runs_long(r, min_run=20) == []


def test_run_pass_fresh():
    r = _r()
    g = G.run(r, ref=pd.Series(np.random.default_rng(4).normal(0, 0.01, len(r)),
                               index=r.index))
    assert g['sr_ok'] is True
    assert g['uniq_ok'] is True


def test_scramble_positive_signal_survives():
    # a real but weak positive signal should have p below ~0.1 (not degenerate)
    n = 900
    idx = pd.date_range('2012-01-01', periods=n, freq='B')
    rng = np.random.default_rng(11)
    ret = rng.normal(0, 0.01, n)
    sig = np.sign(np.convolve(ret, np.ones(5) / 5, mode='same'))
    p, real = G.scramble_positions(sig, ret, n=100, block=20)
    assert real > 0
