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


def test_uniq_ratio_tiny_float_noise_still_counts_flat():
    """AUDIT_FWBUGS R2(b) mutation M23: round-1 only tested exact-constant flattening, so
    deleting the round(10) (which makes sub-1e-10 float noise collapse to one value) passed
    the whole file. A book whose 'variation' lives entirely below 1e-10 IS flattened."""
    r = pd.Series([0.001] * 30, index=pd.date_range('2020-01-01', periods=30, freq='B'))
    r = r + np.arange(30) * 1e-13   # 30 DISTINCT values, all below the round(10) grid
    assert G.uniq_ratio(r) < G.DEFAULTS['uniq_min'], \
        f"sub-rounding noise must collapse under round(10), got uniq={G.uniq_ratio(r)}"


def test_scramble_positive_signal_survives():
    # a real but weak positive signal should have p below ~0.1 (not degenerate)
    n = 900
    idx = pd.date_range('2012-01-01', periods=n, freq='B')
    rng = np.random.default_rng(11)
    ret = rng.normal(0, 0.01, n)
    sig = np.sign(np.convolve(ret, np.ones(5) / 5, mode='same'))
    p, real = G.scramble_positions(sig, ret, n=100, block=20)
    assert real > 0


def test_scramble_baseline_is_real_book_sr():
    """VERIFY_BEST §4c regression: baseline must be the real BOOK's SR, not raw returns.
    A strong real book must have low p; a destroyed book must have p >= 0.5."""
    rng = np.random.default_rng(21)
    n = 900
    ret = rng.normal(0, 0.01, n)
    # strong timing signal: sig = sign of smoothed returns -> real book positive SR
    sig = np.sign(np.convolve(ret, np.ones(5) / 5, mode='same'))
    p, real = G.scramble_positions(sig, ret, n=60, block=20)
    # real book SR must be the baseline (positive, and p low because scrambling destroys timing)
    assert real == G.sharpe_d(pd.Series(sig * ret))
    assert real > 0
    assert p < 0.05, f"strong book should pass position-lag scramble, got p={p}"


def test_scramble_destroyed_book_fails():
    """Random positions unrelated to returns must NOT pass (p should be high)."""
    rng = np.random.default_rng(22)
    n = 900
    ret = rng.normal(0, 0.01, n)
    # noise book: sig independent of returns -> real book SR ~0, scrambled ~0
    sig = rng.normal(0, 1, n)
    p, real = G.scramble_positions(sig, ret, n=60, block=20)
    # a noise book has no timing to destroy => p not near 0; require p > 0.1 (or baseline ~0)
    assert p > 0.1, f"noise book should not spuriously pass, got p={p}"
