"""CAMP_SHORT TDD: shortability_gate correctness (RED->GREEN)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import pytest
from bt.shortability import shortability_gate, mcap_tier, TIERS


def test_names_below_threshold_short_leg_dropped():
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"AAPL": [-0.5, -0.5, -0.5], "TINYCO": [-0.5, -0.5, -0.5]}, index=idx)
    gated, borrow, dropped = shortability_gate(w, {"TINYCO": "NONE"})
    assert dropped == ["TINYCO"]
    assert (gated["TINYCO"] == 0.0).all(), "short leg of un-shortable name must be dropped"
    assert (gated["AAPL"] < 0).all(), "shortable name keeps its short"


def test_borrow_fee_charged_per_tier():
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"A": [-1.0, -1.0, -1.0], "B": [-1.0, -1.0, -1.0]}, index=idx)
    gated, borrow, _ = shortability_gate(w, {"A": "EASY", "B": "HARD"})
    exp = (1.0 * TIERS["EASY"] + 1.0 * TIERS["HARD"]) / 252.0
    assert np.allclose(borrow, exp), f"tiered borrow wrong: {borrow.iloc[0]} != {exp}"


def test_no_lookahead_borrow_same_day_weights():
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"A": [0.0, -1.0, -1.0]}, index=idx)
    _, borrow, _ = shortability_gate(w, {})
    assert borrow.iloc[0] == 0.0, "no short day-1 -> no borrow"
    assert borrow.iloc[1] == TIERS["EASY"] / 252.0, "borrow accrues on the day the short exists"


def test_long_leg_untouched_and_unknown_tier_raises():
    idx = pd.date_range("2020-01-01", periods=2)
    w = pd.DataFrame({"A": [1.0, 1.0], "B": [-0.3, -0.3]}, index=idx)
    gated, _, dropped = shortability_gate(w, {"B": "NONE"})
    assert (gated["A"] == 1.0).all(), "longs must never be touched"
    with pytest.raises(ValueError):
        shortability_gate(w, {"A": "WAT"})


def test_mcap_tier_mapping():
    assert mcap_tier(0.05) == "HARD"
    assert mcap_tier(0.3) == "MEDIUM"
    assert mcap_tier(0.7) == "EASY"
