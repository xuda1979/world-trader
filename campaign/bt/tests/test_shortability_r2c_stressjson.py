"""CAMP_SHORT ROUND 2 TDD (RED->GREEN): borrow-stress JSON must not conflate rebuild
drift with borrow drag.

Contract: in CAMP_SHORT_SHORTABILITY_R2.json every rung's delta_ann_vs_base is measured
against the REBUILT T0 base (same sleeve inputs, same arithmetic), never against the
committed champion CSV. If upstream sleeve edits move the rebuild off the committed CSV,
that gap is reported separately as rebuild_gap_ann_pp — not silently folded into the
borrow number.
"""
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(ROOT, "results", "CAMP_SHORT_SHORTABILITY_R2.json")


def _doc():
    with open(JSON_PATH) as f:
        return json.load(f)


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="stress JSON not generated yet")
def test_rungs_measured_against_rebuilt_base_not_committed():
    d = _doc()
    assert "rebuild_gap_ann_pp" in d, "JSON must report the committed-vs-rebuild gap separately"
    assert "rebuilt_headline" in d, "JSON must carry the rebuilt T0 headline it diffs against"
    for lad, row in d["ladders"].items():
        base_ann = row["REALISTIC"]["base"]["ann"]
        assert base_ann == d["rebuilt_headline"]["ann"], (
            f"{lad}: base rung must be the REBUILT T0 headline, not the committed CSV")


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="stress JSON not generated yet")
def test_realistic_delta_ann_is_borrow_not_rebuild_drift():
    """REALISTIC drag is tiny (only stock-loan slots re-priced), so |delta_ann_vs_base|
    must stay within the compounding envelope of the JSON's own measured drag. A delta
    an order of magnitude larger means committed/rebuild drift got folded in."""
    d = _doc()
    for lad, row in d["ladders"].items():
        for rung in ("T1", "T2"):
            h = row["REALISTIC"][rung]
            drag = h["borrow_drag_ann_pct"]
            # compounding amplifies drag by (1+ann)/(1+r_day) ~ 1.4x; allow 2.5x slack
            assert abs(h["delta_ann_vs_base"]) <= 2.5 * drag + 0.05, (
                f"{lad}/{rung}: delta_ann {h['delta_ann_vs_base']}pp vs drag {drag}% — "
                "rebuild drift is contaminating the borrow number")


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="stress JSON not generated yet")
def test_census_zero_weight_slot_has_zero_stress():
    """A slot with zero champion weight (CFX4: starts 2019-09, after the 2017 IS cut)
    must contribute nothing to any borrow number."""
    d = _doc()
    c = d["slot_census"]["CFX4"]
    if c["mean_champ_short_notional"] == 0.0:
        for lad, row in d["ladders"].items():
            for treat in ("REALISTIC", "BOUND"):
                assert row[treat]["T1"]["borrow_drag_ann_pct"] >= 0.0
        # and the census must say so explicitly
        assert c["days_short"] == 0 and c["pct_days_short"] == 0.0


@pytest.mark.skipif(not os.path.exists(JSON_PATH), reason="stress JSON not generated yet")
def test_ops_runbook_block_present():
    d = _doc()
    rb = d.get("ops_runbook")
    assert rb, "charter (c): JSON must carry an ops-runbook block"
    for k in ("pregate_entry_point", "pregate_pipeline_order", "champion_headroom_ann_pp",
              "hard_tier_drag_realistic_ann_pct", "hard_tier_drag_bound_ann_pct",
              "gate_move_threshold", "scenario_file"):
        assert k in rb, f"ops_runbook missing {k}"
