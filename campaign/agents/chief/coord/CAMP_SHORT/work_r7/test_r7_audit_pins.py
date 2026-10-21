"""CAMP_SHORT R7 pin tests: the charter (a) spot-recompute + (b) capability refresh
numbers. Every assertion re-reads the saved artifacts; run from repo root:
  python3 -m pytest campaign/agents/chief/coord/CAMP_SHORT/work_r7/test_r7_audit_pins.py -q
"""
import json

import pytest

R7 = "/Users/daxu/software/world-trader/campaign/agents/chief/coord/CAMP_SHORT/work_r7"


@pytest.fixture(scope="module")
def laneA():
    return json.load(open(f"{R7}/r7_laneA_cmdt2.json"))


@pytest.fixture(scope="module")
def laneE():
    return json.load(open(f"{R7}/r7_laneE_resbasis.json"))


@pytest.fixture(scope="module")
def cap():
    return json.load(open(f"{R7}/r7_capability.json"))


# ---------------- charter (a) Lane A: HUNT_CMDT2 ----------------
def test_laneA_all_28_metas_reproduce(laneA):
    assert laneA["n_metas"] == 28
    # own-code stats vs meta: 27/28 exact incl. a 2dp rounding tie at 0.295 (dev 0.0002)
    assert laneA["n_all_ok"] == 27
    assert laneA["max_abs_corr_meta"] == 0.053  # |corr_champ| <= 0.053 claim
    assert laneA["n_v2c_fail"] == 28  # 0/28 adoptable verdict


def test_laneA_family_bests_match(laneA):
    assert laneA["family_best_held_book_sr_own"] == {"seasonality": 0.205, "trend": 0.37,
                                                     "spreadmr": 0.122}
    x = laneA["cross_vs_AG2"]
    assert x["family_best_agree"] is True
    assert x["my_w21_lo_vt_sr"] == 0.3701  # held-book, not the superseded 0.465/0.422 prose mix


def test_laneA_prose_defect_numbers_confirmed(laneA):
    s = laneA["prose_defect_spots"]
    # AG2's corrected held-book numbers (their Lane A defect claim)
    assert s["prop_seas_11-03_vt"]["sr_own"] == pytest.approx(-0.196, abs=5e-4)
    assert s["prop_seas_11-03_novt"]["sr_own"] == pytest.approx(-0.109, abs=5e-4)
    assert s["prop_spreadmr_w63_z2_vt"]["sr_own"] == pytest.approx(-0.017, abs=5e-4)
    assert s["prop_trend_w21_lo_vt"]["sr_own"] == pytest.approx(0.370, abs=5e-4)


# ---------------- charter (a) Lane E: RES_BASIS row-137 ----------------
def test_laneE_sha_and_stats(laneE):
    assert laneE["sha_ok"] is True
    assert laneE["stats_own"]["n"] == 4604
    assert laneE["stats_own"]["sr"] == 1.3498
    assert laneE["stats_own"]["ann"] == 13.25
    assert laneE["stats_own"]["mdd"] == -22.29
    assert laneE["stats_own"]["h1"] == 2.182 and laneE["stats_own"]["h2"] == 0.753
    assert laneE["stats_own"]["neg"] == 1
    assert all(laneE["meta_checks"].values()), laneE["meta_checks"]


def test_laneE_is_oos(laneE):
    assert laneE["is_oos_own"]["is_sr"] == 2.145
    assert laneE["is_oos_own"]["oos_sr"] == 0.807


def test_laneE_blend_both_conventions(laneE):
    w25 = laneE["blend_own"]["w0.25"]
    # champ-span fill-0 (meta line + coordinator): dSR +0.199 dAnn +4.21 MDD -6.64
    assert w25["convA_dSR"] == 0.199 and w25["convA_dAnn_pp"] == 4.21
    assert w25["convA_MDD_pct"] == -6.64 and w25["convA_neg"] == 0
    # sleeve-span fill-0: both positive but MDD worse; disclosed, not the meta convention
    assert w25["convB_dSR"] == 0.789 and w25["convB_MDD_pct"] == pytest.approx(-15.59, abs=5e-3)


def test_laneE_v2_battery_reproduces(laneE):
    v = laneE["v2_battery_own_rerun"]
    assert v["sr"] == 1.6031 and v["corr"] == 0.0215
    assert v["leak_corr"] == 0.1071 and v["leak_ok"] is True
    assert v["bp_name"] == "sixty_forty" and v["bp_sr"] == 0.602 and v["bp_ok"] is True
    assert v["PASS"] is True
    assert laneE["rebuild_max_dev_vs_csv"] < 1e-15


def test_laneE_plateau_reproduces(laneE):
    assert laneE["plateau_own_rerun"] == {"21": 1.356, "40": 1.357, "63": 1.35, "90": 1.302,
                                          "126": 1.148}


# ---------------- charter (b) capability refresh ----------------
def test_cap_census_zero_net_short(cap):
    c = cap["B1_census"]
    assert c["pass_"] is True
    assert c["slot_days"] == 62465 and c["n_negative_slot_days"] == 0
    assert c["days"] == 4805 and c["slots"] == 13
    assert c["dualmom_min_w"] > 0  # only single-name panel stays long-only
    assert cap["tree"]["champ_sha16"] == "4358dfab95679b97"


def test_cap_htb_tier_arithmetic(cap):
    h = cap["B2_htb"]
    assert h["ok"] is True
    assert h["embedded_bps_yr"] == pytest.approx(0.2195, abs=5e-4)
    assert h["htb2_bps_yr"] == pytest.approx(0.6586, abs=5e-4)
    assert h["htb8_bps_yr"] == pytest.approx(3.2931, abs=5e-4)


def test_cap_drift_flags_reproduce(cap):
    own = {f["name"]: f for f in cap["B3_drift_flags_own"]}
    pub = {f["name"]: f for f in cap["B3_published"]}
    assert set(own) == set(pub)
    for name, f in own.items():
        assert f["rel_drift_pct"] == pytest.approx(pub[name]["rel_drift_pct"], abs=5e-3), name
        assert f["gt_10pct"] is True


def test_cap_reprices_reproduce(cap):
    own, pub = cap["B3_reprices_own"], cap["B3_reprices_published"]
    for k, v in pub.items():
        assert own[k]["ann_pct"] == pytest.approx(v, abs=5e-4), k
        assert own[k]["neg_years"] == 0
