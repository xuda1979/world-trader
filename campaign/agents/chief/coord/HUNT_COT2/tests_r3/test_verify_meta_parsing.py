"""R3 TDD: meta parsing + comparison must be FAIL-CLOSED on missing keys.

Regression for the bug found auditing verify_cmdt2_r3.py: a meta key that fails to
parse yields NaN, and abs(x - NaN) > tol is False -> the check silently PASSES a
sleeve whose meta is missing/corrupt. The verifier must instead flag any sleeve
whose meta lacks a required numeric key.
"""
import math
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "..", "scripts"))
import HUNT_COT2_verify_cmdt2 as V  # noqa: E402


def test_parse_meta_missing_key_raises_or_flags():
    """A meta missing 'worstyr' must NOT parse as NaN and silently pass."""
    meta = V.parse_meta_text("SR=0.5 ann=1.0% vol=10.0% H1=0.6 H2=0.6 negyrs=2 corr_champ=0.01 n=100\n")
    # The required-numeric-key set must be enforced somewhere; expose it.
    required = {"SR", "ann", "vol", "H1", "H2", "negyrs", "worstyr", "corr_champ", "n"}
    missing = required - set(meta)
    assert missing == {"worstyr"}, f"expected exactly worstyr missing, got missing={missing}"
    # And the comparison helper must treat a missing key as a FAILURE, not a pass.
    assert V.close_or_missing(meta.get("worstyr"), -10.0, 0.2) is False, \
        "missing key vs any claim must be False (fail-closed)"
    assert V.close_or_missing(-10.0, -10.0, 0.2) is True
    assert V.close_or_missing(float("nan"), -10.0, 0.2) is False, "NaN claim must fail too"


def test_close_or_missing_exact_and_nan_claim():
    assert V.close_or_missing(0.234, 0.234, 0.0015) is True
    assert V.close_or_missing(0.234, 0.300, 0.0015) is False
    assert V.close_or_missing(float("nan"), 0.234, 0.0015) is False
