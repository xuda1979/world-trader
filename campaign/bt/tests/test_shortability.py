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


def test_none_tier_keeps_long_leg_only_short_dropped():
    """AUDIT_FWBUGS R2(b) mutation audit (M5): un-shortable means you cannot SHORT the
    name — a long position in it is perfectly holdable and MUST survive the gate untouched.
    Round-1 only tested NONE names from the short side, so a mutation zeroing longs too
    passed the whole file (vacuous coverage)."""
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"LONGY": [0.8, 0.8, 0.8], "SHORTY": [-0.5, -0.5, -0.5]}, index=idx)
    gated, borrow, dropped = shortability_gate(w, {"LONGY": "NONE", "SHORTY": "EASY"})
    assert dropped == ["LONGY"]
    assert (gated["LONGY"] == 0.8).all(), \
        f"NONE-tier long leg must be untouched, got {gated['LONGY'].tolist()}"
    assert (gated["SHORTY"] == -0.5).all()
    assert np.allclose(borrow, 0.5 * TIERS["EASY"] / 252.0)


# ---------------- ROUND 2: shortability_pregate (hunt-template hook) ----------------
from bt.shortability import shortability_pregate


def test_pregate_drops_none_short_leg_and_reelevers_gross():
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"BIG": [1.0, 1.0, 1.0], "TINYCO": [-1.0, -1.0, -1.0]}, index=idx)
    g, borrow, info = shortability_pregate(w, {"TINYCO": "NONE"})
    assert info["dropped"] == ["TINYCO"]
    assert (g["TINYCO"] == 0.0).all(), "un-shortable short leg must be dropped pre-gate"
    assert np.allclose(g.abs().sum(axis=1), 2.0), (
        "preserve_gross: surviving legs re-levered to the original gross")
    assert np.allclose(g["BIG"], 2.0), "long leg takes the dropped short's risk budget"


def test_pregate_borrow_on_survivors_only_and_no_lookahead():
    idx = pd.date_range("2020-01-01", periods=3)
    w = pd.DataFrame({"A": [0.0, -1.0, -1.0], "TINYCO": [-1.0, -1.0, -1.0]}, index=idx)
    g, borrow, _ = shortability_pregate(w, {"TINYCO": "NONE"})
    # day1: A flat -> after relever A=0 stays flat; TINYCO dropped
    assert borrow.iloc[0] == 0.0, "no position day-1 -> no borrow"
    # day2-3: A=-1 re-levered to -2 -> borrow at EASY on 2.0 notional
    assert np.allclose(borrow.iloc[1:], 2.0 * TIERS["EASY"] / 252.0)
    assert np.allclose(g["A"].iloc[1:], -2.0)


def test_pregate_no_dropped_legs_is_identity():
    idx = pd.date_range("2020-01-01", periods=2)
    w = pd.DataFrame({"A": [1.0, -0.5], "B": [-0.5, 1.0]}, index=idx)
    g, borrow, info = shortability_pregate(w, {"A": "EASY", "B": "MEDIUM"})
    assert info["dropped"] == []
    assert np.allclose(g, w), "nothing dropped -> weights unchanged"
    # day1: only B short (0.5 @ MEDIUM); day2: only A short (0.5 @ EASY)
    assert np.allclose(borrow, [0.5 * TIERS["MEDIUM"] / 252.0,
                                0.5 * TIERS["EASY"] / 252.0]), "borrow accrues on surviving shorts"


def test_pregate_unknown_tier_raises_failclosed():
    idx = pd.date_range("2020-01-01", periods=2)
    w = pd.DataFrame({"A": [1.0, 1.0]}, index=idx)
    with pytest.raises(ValueError):
        shortability_pregate(w, {"A": "WAT"})


def test_pregate_preserve_gross_false_keeps_dropped_size():
    idx = pd.date_range("2020-01-01", periods=2)
    w = pd.DataFrame({"BIG": [1.0, 1.0], "TINYCO": [-1.0, -1.0]}, index=idx)
    g, _, info = shortability_pregate(w, {"TINYCO": "NONE"}, preserve_gross=False)
    assert np.allclose(g["BIG"], 1.0), "preserve_gross=False leaves survivors unscaled"
    assert np.allclose(g.abs().sum(axis=1), 1.0)
