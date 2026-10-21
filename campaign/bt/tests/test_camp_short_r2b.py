"""CAMP_SHORT ROUND 2(b) TDD: champion tiered-borrow re-pricing + stock-loan census.

Charter: re-run the champion under TIERED borrow (0.5/1/3 ladders) and quantify
sensitivity; add a borrow-stress scenario JSON to results/ for the ops runbook.
These tests pin (1) the aggregation arithmetic, (2) the stock-loan census of the 13
committed slots, (3) the measured CFX4-zero-weight fact, and (4) the runbook JSON.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
import pytest
from bt.shortability import tier_delta_cost

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r2")
JSON_PATH = f"{ROOT}/campaign/results/CAMP_SHORT_SHORTABILITY_R2.json"


def test_champ_tier_delta_is_aggregated_tier_delta_cost():
    """champ_tier_delta must be exactly the per-slot tier_delta_cost summed over slots."""
    from champ_short import champ_tier_delta
    idx = pd.date_range("2020-01-01", periods=5)
    wg = pd.DataFrame({"A": [0.3] * 5, "B": [-0.2] * 5}, index=idx)
    expo = {"A": pd.Series([0.0, 1.0, 0.5, 0.0, 2.0], index=idx),
            "B": pd.Series([1.0] * 5, index=idx)}
    base = {"A": 0.0, "B": 0.005}
    got = champ_tier_delta(wg, expo, base, tier_rate=0.03)
    want = (tier_delta_cost(expo["A"] * 0.3, 0.0, 0.03)
            + tier_delta_cost(expo["B"] * 0.2, 0.005, 0.03))
    pd.testing.assert_series_equal(got, want, check_names=False)


def test_champ_tier_delta_zero_exposure_and_negative_credit():
    """Slots with no stock-loan exposure contribute nothing; a cheaper tier is a
    NEGATIVE delta (credit) and must not be clipped."""
    from champ_short import champ_tier_delta
    idx = pd.date_range("2020-01-01", periods=3)
    wg = pd.DataFrame({"A": [-0.5] * 3}, index=idx)
    expo = {"A": pd.Series([1.0] * 3, index=idx)}
    d = champ_tier_delta(wg, expo, {"A": 0.02}, tier_rate=0.005)
    assert (d < 0).all(), "cheaper tier must produce a credit, not a clipped zero"
    z = champ_tier_delta(wg, {"A": pd.Series([0.0] * 3, index=idx)}, {"A": 0.0}, 0.03)
    assert (z == 0.0).all()


def test_stockloan_census_pins_champion_slots():
    """Census: only diescrack/CFX4 carry a charged 0.5% cash-borrow line; dualmom and
    A5r2 are long-only BY CONSTRUCTION; every other slot is futures/spot (no stock loan)."""
    from champ_short import CLASS, STOCKLOAN_BASE, NAMES
    assert set(NAMES) == set(CLASS), "census must cover all 13 slots"
    assert CLASS["dualmom"] == "LONG_ONLY_CONSTRUCTION"
    assert CLASS["A5r2"] == "LONG_ONLY_CONSTRUCTION"
    assert set(STOCKLOAN_BASE) == {"diescrack", "CFX4"}
    assert all(v == 0.005 for v in STOCKLOAN_BASE.values())
    for n in NAMES:
        if n not in STOCKLOAN_BASE and CLASS[n] != "LONG_ONLY_CONSTRUCTION":
            assert CLASS[n] == "FUTURES_SPOT_ETF", n


def test_cfx4_champion_weight_identically_zero():
    """CFX4 starts 2019-09 (after IS_END 2017) -> IS SR 0 -> relw 0 -> slot weight 0 for
    every champion day. Its internal borrow can therefore never move the champion."""
    from champ_short import champion_weights
    _, Wg = champion_weights()
    assert float(Wg["CFX4"].abs().max()) == 0.0
    assert float(Wg["diescrack"].max()) > 0.0, "diescrack must be live from champion start"


def test_borrow_stress_json_schema_and_census():
    """Ops-runbook artifact: exists, has both charter ladders with per-rung headline
    metrics under REALISTIC and BOUND treatments, plus the slot census."""
    with open(JSON_PATH) as f:
        j = json.load(f)
    assert j["champion"] == "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
    assert set(j["ladders"]) >= {"050_100_300", "050_200_800"}
    for lad in j["ladders"].values():
        for treat in ("REALISTIC", "BOUND"):
            assert set(lad[treat]) == {"base", "T1", "T2"}, lad.keys()
            for rung in lad[treat].values():
                for k in ("ann", "sr_d", "sr_m", "mdd", "neg_years", "delta_ann_vs_base"):
                    assert k in rung, (treat, rung.keys())
    assert len(j["slot_census"]) == 13
    assert j["champion_validation"]["max_abs_diff_vs_committed"] < 1e-12
    assert j["realistic_vs_bound"]["realistic_worst_delta_ann"] >= \
        j["realistic_vs_bound"]["bound_worst_delta_ann"] - 1e-9, \
        "realistic (few cash-borrow slots) can never cost more than the all-shorts bound"


def test_runbook_rungs_monotone_decreasing_in_tier():
    """Higher borrow tier => weakly lower ann in BOTH treatments (no sign flips):
    delta_ann_vs_base weakly decreasing in tier and never positive (borrow only costs).
    A tiny negative REALISTIC delta (-0.01pp at 3%/8% tiers) is the honest measurement —
    demanding >= 0 would pin zero drag, which the stock-loan census contradicts."""
    with open(JSON_PATH) as f:
        j = json.load(f)
    for lad in j["ladders"].values():
        for treat in ("REALISTIC", "BOUND"):
            a = [lad[treat][r]["ann"] for r in ("base", "T1", "T2")]
            assert a[0] >= a[1] >= a[2] - 1e-9, (treat, a)
            d = [lad[treat][r]["delta_ann_vs_base"] for r in ("T1", "T2")]
            assert d[0] >= d[1], (treat, d)
            assert max(d) <= 1e-9, (treat, d)
            assert min(d) >= -5.0, (treat, d, "5pp = BOUND-envelope sanity cap")


def test_runbook_base_rung_matches_committed_champion():
    """The 'base' rung is the untouched committed champion — pinned, not recomputed."""
    with open(JSON_PATH) as f:
        j = json.load(f)
    b = j["ladders"]["050_100_300"]["REALISTIC"]["base"]
    assert abs(b["delta_ann_vs_base"]) < 1e-12
    assert abs(b["ann"] - j["committed_headline"]["ann"]) < 1e-9
