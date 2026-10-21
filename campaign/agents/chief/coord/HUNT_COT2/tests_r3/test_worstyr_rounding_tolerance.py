"""R3 TDD (RED first): meta is published at 0.1pp granularity; the verifier must not
flag a value as MISMATCH when it differs from the published figure only by that rounding.

Regression: verify_cmdt2_r3.py compared worstyr at 0.005pp and ann/vol at max(5e-4, 3%rel)
against meta lines like `worstyr=-8.4%` (one decimal). A book whose true worst year is
-8.423% publishes -8.4%; diff 0.023pp is the meta's own rounding, not a discrepancy —
the prior session's rerun flagged 11/12 sleeves on exactly this artifact.
"""
import importlib.util
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "verify_r3", os.path.join(HERE, "..", "verify_cmdt2_r3.py"))
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


def test_published_granularity_tolerances_exist():
    """Verifier must expose tolerances >= half the meta's 0.1pp publish granularity."""
    assert getattr(V, "TOL_WORSTYR", 0.0) >= 0.05, \
        "worstyr tolerance must be >= 0.05pp (half of the published 0.1pp granularity)"
    assert getattr(V, "TOL_PCT_PUBLISHED", 0.0) >= 0.05, \
        "ann/vol percentage tolerance floor must be >= 0.05pp"


def test_worstyr_rounding_difference_is_not_a_mismatch():
    """-8.423% computed vs -8.4% published = rounding, must compare True."""
    assert V.close_or_missing(-8.4, -8.423002854231598, V.TOL_WORSTYR) is True
    # but a real discrepancy (0.6pp) must still fail
    assert V.close_or_missing(-9.0, -8.423002854231598, V.TOL_WORSTYR) is False


def test_ann_rounding_difference_is_not_a_mismatch():
    """ann 0.44% computed vs 0.4% published (3%rel floor = 0.012pp too tight)."""
    assert V.close_or_missing(0.4, 0.4401, V.TOL_PCT_PUBLISHED) is True
    assert V.close_or_missing(0.4, 1.2, V.TOL_PCT_PUBLISHED) is False


def test_fail_closed_still_holds():
    """The rounding fix must not reopen the fail-closed hole the other test pins."""
    assert V.close_or_missing(None, -8.4, V.TOL_WORSTYR) is False
    assert V.close_or_missing(float("nan"), -8.4, V.TOL_WORSTYR) is False
