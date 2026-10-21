"""CAMP_SHORT R5 pin tests (work_r5-local — bt/ is a QUIET tree this round per charter;
only AUDIT_FWBUGS/AUDIT_GATES2/AUDIT_CHAMP2 touch bt/). Pins the r5_audit.json artifact:
  1. champion of record acceptance 7/7, sha 4358dfab95679b97, headline 37.1954/3.1810/-6.6922
  2. NO single-name short exposure post-costfix: zero negative slot weights; dualmom
     (the only single-name panel) re-measured long-only on its costfix generator
  3. top gross shares exact (brwt10 22.95% / brwt7 19.96% / brwt5 16.97%)
  4. post-costfix borrow re-price: gates-relevant drag at HARD tier < 0.05pp/yr
Run: python3 -m pytest campaign/agents/chief/coord/CAMP_SHORT/work_r5/test_r5_audit_pins.py -q
"""
import json
import os

import pytest

ROOT = "/Users/daxu/software/world-trader"
J = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r5/r5_audit.json"

pytestmark = pytest.mark.skipif(not os.path.exists(J), reason="run r5_shortability_reaudit.py first")


def _load():
    return json.load(open(J))


def test_champion_of_record_acceptance_unchanged():
    A = _load()["A_acceptance"]
    assert A["ok"] is True and A["n_checks"] == 7
    assert A["sha256_16"] == "4358dfab95679b97"
    assert abs(A["ann_cagr_pct"] - 37.19539675684982) < 1e-9
    assert abs(A["sr"] - 3.180994199561701) < 1e-9
    assert abs(A["mdd_pct"] - (-6.692185534307193)) < 1e-9
    assert A["neg_years"] == 0 and A["n_days"] == 4805
    assert A["cost_model"] == "full_dw" and abs(A["cost_ratio"] - 1.0) < 1e-9


def test_no_single_name_short_exposure_post_costfix():
    r = _load()
    B = r["B_weights_decomposition"]
    assert B["pin_max_dev_vs_committed_champion"] < 1e-12
    assert B["any_net_short_slot_days"] == 0 and B["wmin_slot_level"] >= -1e-12
    # dualmom is the ONLY single-name equity slot; its costfix generator is long-only
    D = r["D_dualmom"]
    assert D["n_negative_weights_in_target_matrix"] == 0
    assert D["n_negative_weights_in_live_T1_stream"] == 0
    assert D["min_weight"] >= 0.0


def test_top_gross_shares_exact():
    shares = _load()["B_weights_decomposition"]["top_gross_shares"]
    assert list(shares)[:3] == ["brwt10", "brwt7", "brwt5"]
    assert abs(shares["brwt10"] - 0.22949108882496253) < 5e-3   # 22.95%
    assert abs(shares["brwt7"] - 0.19957363459965872) < 5e-3    # 19.96%
    assert abs(shares["brwt5"] - 0.1697372464420777) < 5e-3     # 16.97%


def test_post_costfix_borrow_drag_immaterial_at_every_tier():
    F = _load()["F_borrow_repricing"]
    for slot in ("diescrack", "CFX4"):
        for rung in ("EASY_T0", "MEDIUM_T1", "HARD_T2"):
            assert F[slot][f"delta_ann_pp_{rung}"] < 0.05, (slot, rung)
    assert F["CFX4"]["relw_committed"] == 0.0            # zero champion weight, still
    assert F["diescrack"]["delta_ann_pp_EASY_T0"] == 0.0  # base == EASY: no delta


def test_harness_c5_green_with_exact_shares():
    C5 = _load()["E_harness_battery"]["C5"]
    assert C5 is not None and C5["ok"] is True
    assert "13/13 instrument classes verified" in C5["msg"]
    assert "dualmom LONG-ONLY" in C5["msg"]
    for n in ("C1", "C2", "C3", "C4", "C5", "C6", "C7"):
        assert _load()["E_harness_battery"][n]["ok"] is True, n
