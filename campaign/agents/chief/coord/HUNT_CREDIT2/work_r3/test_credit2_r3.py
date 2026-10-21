"""TDD: HUNT_CREDIT2 round-3 hunt machinery (written BEFORE the implementation; RED->GREEN).

Pins the four behaviors the R3 hunts depend on, each of which could silently leak or
mis-state results:
  1. carry accrual: total return = price return + yield/365, yield lagged T+1 (publish-safe).
  2. mean-reversion signal is ANTI-momentum (long after down-moves), weekly resample uses
     only data up to the decision date.
  3. no-lookahead: books rebuilt from series truncated at T reproduce the full-sample
     weights exactly on the overlap (catches rolling-max / resample / accrual leaks).
  4. generic-control kill-test calibration: the vol-matched random-mask ensemble must
     PASS (real >> masks) on synthetic conditional alpha and FAIL (real ~ masks) on
     pure noise — i.e. the kill-test can actually kill.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np
import pandas as pd
import pytest

import HUNT_CREDIT2_round3 as cr3


def _prices(n=800, seed=3, drift=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-05", periods=n)
    r = pd.Series(rng.normal(drift, 0.01, n), index=idx)
    return 100 * (1 + r).cumprod(), r


# ---- 1. carry accrual -----------------------------------------------------------------------
def test_carry_accrual_adds_yield_and_lags_it():
    """Flat price + 5%/yr yield -> TR daily ret == 0.05/365 (to fp tol); the accrual on day t
    must come from the yield known at t-1 (shift(1)), so a one-day yield spike lands one day
    later in the TR series."""
    idx = pd.bdate_range("2015-01-05", periods=400)
    px = pd.Series(100.0, index=idx)                       # flat price
    yld = pd.Series(5.0, index=idx)                        # FRED levels: 5.0 = 5%/yr
    yld.iloc[300] = 50.0                                   # one-day spike (50%/yr)
    tr = cr3.total_return(px, yld)
    body = tr.dropna().iloc[1:299]
    assert np.allclose(body, 0.05 / 365, atol=1e-12), f"accrual wrong: {body.iloc[0]:.3e}"
    # spike at t=300 must appear in TR at t=301, NOT t=300
    assert abs(tr.iloc[300] - 0.05 / 365) < 1e-12, "same-day yield used (lookahead)"
    assert abs(tr.iloc[301] - 0.50 / 365) < 1e-12, "lagged yield not honored"


# ---- 2. mean-reversion signal ---------------------------------------------------------------
def test_meanrev_signal_is_antimomentum():
    """Up-trending synthetic price -> flat (never long). Down-trending -> long (after the
    k-1 day rolling warmup, where the signal is flat by design). This is the charter's
    'buy-the-dip, NOT momentum' requirement pinned as a unit test."""
    n = 600
    up = pd.Series(np.linspace(100, 200, n), index=pd.bdate_range("2015-01-05", periods=n))
    dn = up.iloc[::-1].set_axis(up.index)
    k = 20
    sig_up = cr3.meanrev_signal(up, k=k).iloc[k:]     # exclude rolling warmup
    sig_dn = cr3.meanrev_signal(dn, k=k).iloc[k:]
    assert (sig_up == 0).all(), "longed an uptrend (momentum leaked in)"
    assert (sig_dn == 1).all(), "did not long a persistent downtrend"


def test_weekly_signal_uses_only_past():
    """Weekly (W-FRI) resample of the daily signal must equal the daily signal AT each Friday
    — resampling cannot introduce values that the Friday close didn't know."""
    px, _ = _prices(900, seed=11)
    daily = cr3.meanrev_signal(px, k=20)
    weekly = cr3.to_weekly(daily)
    fridays = weekly.dropna().index
    assert (weekly.dropna() == daily.reindex(fridays)).all(), "weekly resample peeked ahead"


# ---- 3. no-lookahead truncated rebuilds -----------------------------------------------------
def _assert_trunc_rebuild(builder, T="2018-06-29"):
    Wf, Rf = builder(trunc=None)
    Wt, Rt = builder(trunc=T)
    ov = Rt.index
    pd.testing.assert_frame_equal(Wf.reindex(ov).round(12), Wt.round(12),
                                  check_freq=False)


def test_no_lookahead_truncated_rebuilds():
    px_a, _ = _prices(900, seed=5)
    px_b, _ = _prices(900, seed=6)
    yld_a = pd.Series(0.06, index=px_a.index)
    yld_b = pd.Series(0.03, index=px_b.index)
    _assert_trunc_rebuild(lambda trunc: cr3.book_spread_momentum(px_a, px_b, k=63, trunc=trunc))
    _assert_trunc_rebuild(lambda trunc: cr3.book_carry(px_a, yld_a, px_b, yld_b, trunc=trunc))
    _assert_trunc_rebuild(lambda trunc: cr3.book_meanrev(px_a, k=20, trunc=trunc))


# ---- 4. generic-control (vol-matched random-mask) kill-test calibration ---------------------
def test_mask_control_kills_noise_and_keeps_alpha():
    """On pure-noise masks+returns the control must NOT separate real from random (no false
    adopt); on a series with genuine conditional alpha (long only after negative days) the
    real signal must sit above the 95th pctile of matched random masks."""
    rng = np.random.default_rng(9)
    idx = pd.bdate_range("2015-01-05", periods=2000)
    # pure noise book
    noise = pd.Series(rng.normal(0, 0.01, len(idx)), index=idx)
    mask = pd.Series((rng.random(len(idx)) < 0.5).astype(float), index=idx)
    p_noise = cr3.mask_control_pvalue(noise, mask, on_frac=0.5, n=100, seed=1)
    assert p_noise > 0.05, "control passed on pure noise (kill-test is toothless)"
    # genuine conditional alpha: +40bp extra on masked days
    alpha = noise + mask * 0.004
    p_alpha = cr3.mask_control_pvalue(alpha, mask, on_frac=0.5, n=100, seed=1)
    assert p_alpha <= 0.05, f"control failed to detect real alpha (p={p_alpha:.3f})"
