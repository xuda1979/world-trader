"""CAMP_SHORT ROUND 3(a): library borrow census — fail-closed contract tests.

Charter: top-30 sleeve_library sleeves by SR (+ BLEND_CANDIDATE_SUBMISSION intake):
reconstruct or FAIL-CLOSED-flag short legs (SHORT_LEG_UNKNOWN = cannot be integrated,
loud); tier ladder 0.5/2/8% + NONE-tier drops; per-sleeve ann drag; which survive
integration-grade borrow pricing. Artifact: campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json
"""
import hashlib
import json
import os

import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
JSON_PATH = f"{ROOT}/campaign/results/CAMP_SHORT_LIBRARY_BORROW_CENSUS.json"
LIB = f"{ROOT}/campaign/results/sleeve_library"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

INTAKE = ["MSSW", "CRX1030", "A_rs", "A11", "COMP50d", "CMDTrot_h2"]
RENET_TOL = 2e-4


def _load():
    with open(JSON_PATH) as f:
        return json.load(f)


def _rows(j):
    return j["sleeves"]


# ------------------------------------------------------------------ structure
def test_json_exists_and_is_round3(tmp_path=None):
    if not os.path.exists(JSON_PATH):
        pytest.fail("CAMP_SHORT_LIBRARY_BORROW_CENSUS.json not written yet (RED phase)")
    j = _load()
    assert j["agent"] == "CAMP_SHORT"
    assert j["round"] == 3


def test_covers_top30_library_plus_intake():
    j = _load()
    rows = _rows(j)
    top30 = test_top30_selection_is_true_sr_ranking.__wrapped__() if False else None
    # every intake candidate present
    for c in INTAKE:
        assert c in rows, f"BLEND_CANDIDATE_SUBMISSION intake {c} missing"
    # rows beyond the 30 library files are exactly the intake-only candidates
    lib_files = {f[:-4] for f in os.listdir(LIB) if f.endswith(".csv")}
    extra = set(rows) - lib_files
    assert extra == set(INTAKE), extra
    # the 30 library files that made the census are the SR top-30 (test below pins the set)
    assert len([k for k in rows if k in lib_files]) == 30


def test_top30_selection_is_true_sr_ranking():
    """The 30 library rows must BE the top-30 by recomputed SR_d of the CSVs."""
    j = _load()
    srs = {}
    for f in os.listdir(LIB):
        if not f.endswith(".csv"):
            continue
        df = pd.read_csv(os.path.join(LIB, f), index_col=0)
        s = pd.to_numeric(df.iloc[:, 0], errors="coerce")
        s.index = pd.to_datetime(df.index, errors="coerce")
        s = s.dropna()
        if len(s) < 100 or s.std(ddof=1) <= 0:
            continue
        srs[f[:-4]] = float(s.mean() / s.std(ddof=1) * (252 ** 0.5))
    top30 = set(sorted(srs, key=lambda k: -srs[k])[:30])
    rows = {k: v for k, v in _rows(j).items() if not v.get("is_intake")}
    assert set(rows) == top30, (
        "census library set != top-30 by SR: "
        f"missing={sorted(top30 - set(rows))} extra={sorted(set(rows) - top30)}")


def test_every_row_has_valid_measurement_field():
    j = _load()
    for name, r in _rows(j).items():
        assert r["measurement"] in {"MEASURED", "STRUCTURAL", "SHORT_LEG_UNKNOWN"}, name


def test_fail_closed_rows_are_loud_and_not_integrable():
    j = _load()
    bad = []
    for name, r in _rows(j).items():
        if r["measurement"] == "SHORT_LEG_UNKNOWN":
            if r.get("verdict") != "NOT_INTEGRABLE" or not r.get("fail_closed_reason"):
                bad.append(name)
    assert not bad, f"SHORT_LEG_UNKNOWN rows must be NOT_INTEGRABLE with a reason: {bad}"


def test_no_integration_ok_without_a_known_short_leg():
    j = _load()
    bad = [n for n, r in _rows(j).items()
           if r.get("verdict") == "INTEGRATION_OK" and r["measurement"] == "SHORT_LEG_UNKNOWN"]
    assert not bad, f"fail-closed violation: {bad}"


def test_measured_rows_have_validated_renet():
    j = _load()
    for name, r in _rows(j).items():
        if r["measurement"] != "MEASURED":
            continue
        rn = r.get("renet") or {}
        assert rn.get("ok") is True, f"{name} marked MEASURED without re-net validation"
        if rn.get("mode") == "activity_coverage":
            assert float(rn.get("coverage", 0.0)) >= 0.999, name
        else:
            assert float(rn.get("max_diff", 1.0)) <= RENET_TOL, name


# ------------------------------------------------------------------ ladder math
def test_ladder_delta_arithmetic_exact():
    """delta_ann_pp must equal (tier_rate - base_rate) * mean_short_frac * 100 exactly —
    valid whether the sleeve's base is 0 (drag grows with tier) or above a tier
    (delta flips sign). base_borrow_ann is /yr as a fraction."""
    j = _load()
    TIER = {"0.5%": 0.005, "2%": 0.02, "8%": 0.08}
    for name, r in _rows(j).items():
        if not r.get("borrow_applies"):
            continue
        frac = r["short_notional"]["mean_frac"]
        if frac is None:
            continue
        base = r["base_borrow_ann"]
        for k, tr in TIER.items():
            want = (tr - base) * frac * 100.0
            got = r["ladder"][k]["delta_ann_pp"]
            assert abs(got - want) < 1e-4, f"{name} {k}: {got} != {want}"


def test_no_stock_loan_classes_have_zero_delta():
    zero_classes = {"FUTURES_MACRO_SYNTH", "FACTOR_SYNTH", "SPREAD_SYNTH",
                    "LONG_ONLY", "PERP_CRYPTO"}
    j = _load()
    for name, r in _rows(j).items():
        if r["instrument_class"] in zero_classes:
            for k in ("0.5%", "2%", "8%"):
                assert r["ladder"][k]["delta_ann_pp"] == 0.0, (
                    f"{name} ({r['instrument_class']}) charged a stock-loan delta")


def test_xgb1y_short_book_is_caught_as_material():
    """XGB1y shorts the BOTTOM DECILE of a ~660-name panel, monthly, |short| = 1.0 NAV.
    Its published net (both the monthly book and the flattened-daily spread) charges
    ZERO borrow. The census must price that leg: the ladder equals the full tier drag
    (base 0) and 8% HARD must cost ~8%/yr of NAV on a 15.3% ann sleeve."""
    r = _load()["sleeves"]["XGB1y_deploy"]
    assert r["borrow_applies"] is True
    assert r["short_notional"]["mean_frac"] >= 0.95
    assert abs(r["ladder"]["8%"]["drag_ann_pp"] - 8.0) < 0.01
    assert abs(r["ladder"]["8%"]["delta_ann_pp"] - 8.0) < 0.01
    assert r["verdict"] == "INTEGRATION_RISK"


def test_ls_n10r14_borrow_already_charged_no_double_count():
    """n10r14's generator charges (DFF-rebate)+ETB borrow already and holds |short| ~ 0.5
    at gross 1.0. Its measured base (>= EASY 0.5%) means the EASY rung delta must NOT
    be a fresh charge (<= 0), and its verdict must not be INTEGRATION_OK."""
    r = _load()["sleeves"]["ls_n10r14_2018"]
    assert r["measurement"] == "STRUCTURAL"
    assert 0.35 <= r["short_notional"]["mean_frac"] <= 0.65
    assert r["base_borrow_ann"] >= 0.005
    assert r["ladder"]["0.5%"]["delta_ann_pp"] <= 0.0
    assert r["verdict"] == "INTEGRATION_RISK"


def test_risk_parity_is_long_only():
    r = _load()["sleeves"]["Risk_Parity_Bridgewater"]
    assert r["instrument_class"] == "LONG_ONLY"
    assert r["short_notional"]["mean_frac"] == 0.0


def test_ap_gold_fails_closed():
    r = _load()["sleeves"]["AP_gold"]
    assert r["measurement"] == "SHORT_LEG_UNKNOWN"
    assert r["verdict"] == "NOT_INTEGRABLE"


def test_mssw_fails_closed():
    r = _load()["sleeves"]["MSSW"]
    assert r["measurement"] == "SHORT_LEG_UNKNOWN"
    assert r["verdict"] == "NOT_INTEGRABLE"


def test_intake_already_priced_sleeves_report_base_not_double_charge():
    """Intake sleeves whose meta declares '+0.5%/yr borrow' must show zero delta at
    the EASY rung (their published net already carries it)."""
    j = _load()
    for name in ("CMDTrot_h2",):
        r = j["sleeves"][name]
        assert abs(r["ladder"]["0.5%"]["delta_ann_pp"]) < 1e-9, name


def test_summary_consistent_with_rows():
    j = _load()
    rows = _rows(j)
    s = j["summary"]
    assert s["n_rows"] == len(rows)
    assert s["n_unknown"] == sum(1 for r in rows.values()
                                 if r["measurement"] == "SHORT_LEG_UNKNOWN")
    assert "AP_gold" in s["unknown_names"]
    assert s["n_integration_risk"] == sum(1 for r in rows.values()
                                          if r["verdict"] == "INTEGRATION_RISK")


def test_champion_untouched_by_census_run():
    """The census must not mutate the champion (R2 lesson: blast radius discipline)."""
    j = _load()
    want = j["champion_reemit"]["champion_sha256_at_run"]
    with open(CHAMP, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == want
