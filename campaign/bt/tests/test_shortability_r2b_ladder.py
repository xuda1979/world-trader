"""CAMP_SHORT ROUND 2(b) TDD (RED->GREEN): tier-ladder re-pricing of an existing book.

The champion carries borrow INSIDE pre-netted sleeve files at flat 0.5%/yr (or not at
all). Re-pricing under a TIERED borrow ladder is pure arithmetic on the measured short
notional stream: delta_cost_t = short_notional_t * (tier_rate - base_rate) / 252.
These tests pin that arithmetic fail-closed BEFORE the champion re-run uses it.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import pytest
from bt.shortability import tier_delta_cost, LADDER_050_100_300, LADDER_050_200_800


def _sn(vals, freq="D", start="2020-01-01"):
    idx = pd.date_range(start, periods=len(vals), freq=freq)
    return pd.Series(vals, index=idx, dtype=float)


def test_tier_delta_matches_hand_math():
    """1.0 short notional at tier 3% vs 0.5% already charged = +2.5%/yr on that notional."""
    sn = _sn([1.0] * 252)
    d = tier_delta_cost(sn, base_rate=0.005, tier_rate=0.03)
    expected_daily = (0.03 - 0.005) / 252.0
    assert abs(d.iloc[0] - expected_daily) < 1e-15
    assert abs(d.mean() * 252 - 0.025) < 1e-12


def test_tier_delta_negative_when_tier_below_base():
    """A tier BELOW what was already charged must give a NEGATIVE delta (credit) — never clipped."""
    sn = _sn([0.8] * 10)
    d = tier_delta_cost(sn, base_rate=0.02, tier_rate=0.005)
    assert (d < 0).all()
    assert abs(d.mean() * 252 - 0.8 * (0.005 - 0.02)) < 1e-12


def test_tier_delta_zero_when_tier_equals_base_and_zero_notional():
    assert (tier_delta_cost(_sn([1.0] * 5), 0.005, 0.005) == 0.0).all()
    assert (tier_delta_cost(_sn([0.0] * 5), 0.005, 0.08) == 0.0).all()


def test_tier_delta_failclosed_on_negative_notional_and_nan():
    with pytest.raises(ValueError):
        tier_delta_cost(_sn([-0.1] * 5), 0.005, 0.03)
    with pytest.raises(ValueError):
        s = _sn([1.0, np.nan, 1.0, 1.0, 1.0])
        tier_delta_cost(s, 0.005, 0.03)


def test_ladder_constants_and_shape():
    """Charter ladders: (0.5/1/3)% and the R1 calibration (0.5/2/8)%. Tier 0 == base."""
    assert LADDER_050_100_300 == {"T0": 0.005, "T1": 0.01, "T2": 0.03}
    assert LADDER_050_200_800 == {"T0": 0.005, "T1": 0.02, "T2": 0.08}
    for lad in (LADDER_050_100_300, LADDER_050_200_800):
        sn = _sn([0.6] * 50)
        d0 = tier_delta_cost(sn, 0.005, lad["T0"])
        assert (d0 == 0.0).all(), "base tier must be a no-op (book already priced there)"


def test_tier_delta_annualized_ann_drag_on_mixed_stream():
    """Mixed stream: mean delta x 252 equals hand-computed annual drag."""
    sn = _sn([0.0, 1.0, 0.5, 0.0, 2.0])
    d = tier_delta_cost(sn, 0.005, 0.03)
    assert abs(d.mean() * 252 - (0.025 * sn.mean())) < 1e-12
