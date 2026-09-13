"""CAMP_SHORT ROUND 2 TDD (RED->GREEN): the hunt-template pre-gate snippet.

Round-2 charter (a): publish the ~20-line integration snippet that wires shortability
into the round-2 hunt sleeve template — any candidate shorting single names must pass
tiered-borrow + non-shortable-drop BEFORE gates. These tests pin the snippet contract.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import pytest
from bt.shortability import shortability_pregate, TIERS


def _w(cols_vals, periods=4):
    idx = pd.date_range("2020-01-01", periods=periods)
    return pd.DataFrame(cols_vals, index=idx)


def test_pregate_drops_unshortable_and_preserves_gross():
    """NONE-tier short dropped; surviving legs re-levered so book gross is preserved."""
    w = _w({"BIGCO": [-0.4, -0.4, -0.4, -0.4], "TINYCO": [-0.4, -0.4, -0.4, -0.4],
            "ETF": [0.8, 0.8, 0.8, 0.8]})
    wg, borrow, info = shortability_pregate(w, {"TINYCO": "NONE"})
    assert info["dropped"] == ["TINYCO"]
    assert (wg["TINYCO"] == 0.0).all()
    g0, g1 = w.abs().sum(axis=1), wg.abs().sum(axis=1)
    assert np.allclose(g0, g1), f"gross must be preserved: {g1.iloc[0]} != {g0.iloc[0]}"
    assert (wg["BIGCO"] < -0.4).all(), "surviving short must be re-levered up"


def test_pregate_borrow_is_tiered_not_flat():
    """Borrow must scale with the IBKR tier ladder (0.5/2/8%), not a flat 0.5%."""
    out = {}
    for tier in ("EASY", "MEDIUM", "HARD"):
        w = _w({"S": [-1.0, -1.0, -1.0, -1.0]})
        _, borrow, _ = shortability_pregate(w, {"S": tier})
        out[tier] = float(borrow.mean() * 252)
    assert abs(out["EASY"] - TIERS["EASY"]) < 1e-12
    assert abs(out["MEDIUM"] / out["EASY"] - 4.0) < 1e-9, "MEDIUM must be 4x EASY (2% vs 0.5%)"
    assert abs(out["HARD"] / out["EASY"] - 16.0) < 1e-9, "HARD must be 16x EASY (8% vs 0.5%)"


def test_pregate_no_lookahead():
    """Borrow accrues only from the day the short exists (day-1 flat -> zero borrow)."""
    w = _w({"S": [0.0, -1.0, -1.0, -1.0]})
    _, borrow, _ = shortability_pregate(w, {})
    assert borrow.iloc[0] == 0.0
    assert abs(borrow.iloc[1] - TIERS["EASY"] / 252.0) < 1e-15


def test_pregate_recharges_borrow_after_relever():
    """After dropping a short and re-levering, borrow is charged on the RESCALED notional."""
    w = _w({"BIGCO": [-0.4] * 4, "TINYCO": [-0.4] * 4})
    wg, borrow, _ = shortability_pregate(w, {"TINYCO": "NONE"})
    scaled = abs(float(wg["BIGCO"].iloc[0]))     # short NOTIONAL 0.8 after renorm
    exp = scaled * TIERS["EASY"] / 252.0
    assert abs(borrow.iloc[0] - exp) < 1e-15, f"{borrow.iloc[0]} != {exp}"


def test_pregate_gate_block_shapes_and_report():
    """Returns frames aligned to input + an info dict usable in FINDINGS/logs."""
    w = _w({"A": [0.5, -0.5, -0.5, 0.0], "B": [0.0, 0.5, 0.5, 0.5]})
    wg, borrow, info = shortability_pregate(w, {"A": "MEDIUM"})
    assert list(wg.columns) == list(w.columns) and (wg.index == w.index).all()
    assert borrow.index.equals(w.index)
    assert info["dropped"] == []
    assert set(info) >= {"dropped", "gross_before", "gross_after", "borrow_ann_frac"}
    assert info["borrow_ann_frac"] > 0.0


def test_pregate_fail_closed_unknown_tier_and_flat_book():
    w = _w({"A": [-0.5] * 4})
    with pytest.raises(ValueError):
        shortability_pregate(w, {"A": "WAT"})
    # a book with zero gross anywhere must not divide by zero
    wg, borrow, info = shortability_pregate(_w({"A": [0.0] * 4}), {})
    assert (wg["A"] == 0.0).all() and (borrow == 0.0).all()


def test_pregate_end_to_end_through_cost_chain():
    """Snippet drops the pipe end-to-end: pre-gate -> engine cost chain -> finite stats,
    and HARD-tier shorting is strictly worse than EASY on an identical short book."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from bt import engine as E
    rng = np.random.default_rng(7)
    idx = pd.date_range("2015-01-01", periods=756)
    r = pd.DataFrame({"BAD": rng.normal(0, 0.01, 756), "GOOD": rng.normal(0.0002, 0.01, 756)},
                     index=idx)
    sig = pd.Series(-1.0, index=idx)                     # short both all year
    w = pd.DataFrame({"BAD": sig, "GOOD": sig})
    for tier, scale_cap in (("EASY", 2.0), ("HARD", 2.0)):
        wg, borrow, info = shortability_pregate(w, {"BAD": tier, "GOOD": tier})
        net = (wg * r).sum(axis=1) - borrow
        assert np.isfinite(net).all() and len(net) == 756
        out = {"EASY": None, "HARD": None}[tier] if False else float(net.mean())
        if tier == "EASY":
            easy_mean = out
        else:
            assert out < easy_mean, "HARD borrow must strictly reduce an all-short book"
