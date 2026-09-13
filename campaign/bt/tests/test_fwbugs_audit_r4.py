"""AUDIT_FWBUGS R4: kill the M22 max_dd NaN-poison mutant family (charter R4).

R2's mutant pass left M22_maxdd_nanpoison as the suite's only VACUOUS-EVERYWHERE survivor.
R3 proved the literal mutant `eq[r.isna()] = np.nan` is an EQUIVALENT mutant (identical on
180/180 randomized NaN panels — cumprod already carries NaN at holes, so the write is a
no-op) and pinned the max_dd NaN contract instead. What R3 never did is DEMONSTRATE a test
that fails under the killable members of the M22 family. This file closes that with RED
fixtures against three distinguishable fail-open/lie mutants (each verified against the
shipped implementation via mutant injection, work/r4/mutate4.py):

  M22d  any-NaN -> return 0.0        ("perfect drawdown" lie, same fail-open class as the
                                      R1 neg_years / R2 ann_geo bugs)
  M22e  dd.min(skipna=False)         (a single hole -> NaN: unmeasurable answer where a
                                      real drawdown exists = fail-closed overreach that
                                      would false-FAIL honest books)
  M22f  eq = (1 + r).cumprod(skipna=False)  (NaN poisons equity downstream: drawdowns
                                      AFTER a hole vanish -> min becomes 0.0)

Kill matrix (measured, see FINDINGS R4): the charter's literal NaN-year fixture kills
M22d/M22e; a NaN hole BEFORE the trough is required to kill M22f; all-NaN pins the
fail-closed NaN answer (kills M22d only). All fixtures are hand-computable — no random
data — so a failure names the exact wrong number.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bt.metrics import max_dd  # noqa: E402

IDX = pd.date_range("2020-01-01", periods=256, freq="B")


def _nan_year_series():
    """3 real days (peak then a -10% day) + a WHOLE MISSING YEAR (252 NaN) + 1 real day.
    Equity: 1.01, 1.0201, 0.91809, flat through the hole, 0.9364518. The -10% drawdown is
    real and must survive the hole: max_dd == -0.10."""
    vals = [0.01, 0.01, -0.10] + [np.nan] * 252 + [0.02]
    return pd.Series(vals, index=pd.date_range("2020-01-01", periods=len(vals), freq="B"))


def test_max_dd_nan_year_does_not_erase_the_real_drawdown():
    """CHARTER R4 fixture: a NaN year adjacent to real drawdown must not poison the answer.
    M22d would lie 0.0 (perfect drawdown); M22e would say NaN (lost measurement)."""
    d = max_dd(_nan_year_series())
    assert np.isfinite(d), f"NaN year made a measured drawdown unmeasurable: {d}"
    assert d == pytest.approx(-0.10, abs=1e-9), f"NaN year changed the drawdown: {d}"


def test_max_dd_nan_hole_before_trough_still_measured():
    """M22f killer (cumprod(skipna=False)): equity dies at the hole so the LATER -10% day
    never enters the drawdown path and the mutant reports 0.0. Shipped semantics carry
    equity flat through the hole, so the trough after it is measured."""
    r = pd.Series([0.05, np.nan, -0.10], index=pd.date_range("2020-01-01", periods=3))
    d = max_dd(r)
    assert np.isfinite(d), f"hole made the post-hole drawdown unmeasurable: {d}"
    assert d == pytest.approx(-0.10, abs=1e-9), f"hole erased the post-hole drawdown: {d}"
    # and the answer is exactly the hole-filled computation (pandas skipna semantics)
    assert d == pytest.approx(max_dd(r.fillna(0.0)), abs=1e-12)


def test_max_dd_all_nan_year_fails_closed_nan():
    """A wholly unmeasurable year -> NaN, never the 0.0 'perfect drawdown' lie (M22d)."""
    r = pd.Series(np.nan, index=pd.date_range("2020-01-01", periods=252, freq="B"))
    assert np.isnan(max_dd(r))


def test_max_dd_no_nan_control_unchanged():
    """Control: the NaN machinery must not perturb the clean path (guards against a
    future 'fix' that zeroes dd when any NaN was ever seen in the file's history)."""
    r = pd.Series([0.01, 0.01, -0.10, 0.02], index=pd.date_range("2020-01-01", periods=4))
    assert max_dd(r) == pytest.approx(-0.10, abs=1e-9)
