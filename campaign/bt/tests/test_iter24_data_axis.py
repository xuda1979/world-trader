"""ITER24 data-axis closure pins (2026-09-19, coordinator).

Reality-pins, GREEN by construction (like test_iter23_gridedge_closure.py): they freeze the
computed facts of the ITER24 honest negative so no later session can silently re-litigate
them. Their ability to FAIL was demonstrated by a recorded mutation run before this file was
finalized (see FINDINGS.md). No production code was changed in ITER24.

Facts pinned (campaign/agents/chief/coord/ITER24_DA/FINDINGS.md):
1. The champion of record bytes are untouched by ITER24 (sha16 8559fa55ee9a3417).
2. The revealed IS-argmax book (13-pool + bund_02y) FAILS the OOS police: FS SR below the
   incumbent and only 2/5 positive 2017+ bin dSRs -> REJECT, honest negative.
3. The driver log records 11/28 admitted (all F1 bund + cad 2y/3y/5y) and a REJECT verdict;
   28 candidate sleeves exist as reproducible artifacts.
"""
import hashlib
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CHAMP = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
DA = ROOT + "/campaign/agents/chief/coord/ITER24_DA"
CAND = DA + "/candidate_bund_02y_daily.csv"
INC_SR = 3.751429


def _sr(x):
    return float(x.mean() / x.std(ddof=1) * np.sqrt(252))


def test_champion_of_record_unchanged_by_iter24():
    # Re-anchored 2026-09-19 (ITER43 adoption): the live champion legitimately changed to
    # e67446186e269b88; the ITER24-era bytes (untouched by ITER24) are preserved byte-exact
    # in the ITER43 prior_champion_backup daily (8559fa55ee9a3417).
    # ITER47 re-anchor (2026-09-19): live champion -> 3c456aa53193eb89 (e67446186e269b88 preserved
    # in coord/ITER47_A5R2_VTEXT/prior_champion_backup).
    sha = hashlib.sha256(open(CHAMP, "rb").read()).hexdigest()[:16]
    assert sha == "cfa9ec4d38158691", f"live champion bytes changed: {sha}"
    bk = (ROOT + "/campaign/agents/chief/coord/ITER43_A5R2_VT"
          + "/prior_champion_backup/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
    sha_bk = hashlib.sha256(open(bk, "rb").read()).hexdigest()[:16]
    assert sha_bk == "8559fa55ee9a3417", f"ITER24-era champion not preserved: {sha_bk}"


def test_iter24_argmax_book_fails_oos_police():
    # Re-anchored 2026-09-19 (ITER43): the incumbent side is the champion OF THE ITER24 ERA
    # -- the preserved prior_champion_backup daily (8559fa55ee9a3417) -- not the live
    # champion; the historical REJECT verdict stays a REJECT.
    champ = pd.read_csv(ROOT + "/campaign/agents/chief/coord/ITER43_A5R2_VT"
                        + "/prior_champion_backup/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True).iloc[:, 0]
    cand = pd.read_csv(CAND, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([champ.rename("i"), cand.rename("c")], axis=1, join="inner")
    assert len(j) == 4806
    inc_s, cand_s = _sr(j["i"]), _sr(j["c"])
    assert cand_s < inc_s, "argmax book must NOT beat the incumbent on FS SR"
    dsrc = []
    for a, b in [("2017", "2018"), ("2019", "2020"), ("2021", "2022"),
                 ("2023", "2024"), ("2025", "2026")]:
        m = j[(j.index >= a + "-01-01") & (j.index <= b + "-12-31")]
        dsrc.append(_sr(m["c"]) - _sr(m["i"]))
    assert sum(1 for d in dsrc if d > 0) < 4, "OOS police requires 4/5 positive; argmax had 2/5"
    # frozen record values (driver log), so drift in either direction is visible
    assert abs(cand_s - 3.728158) < 5e-6
    assert abs(dsrc[1] - (-0.0939)) < 1e-3 and abs(dsrc[3] - 0.1381) < 1e-3


def test_iter24_audit_artifacts_and_admission_count():
    log = open(DA + "/driver_2026-09-19.log").read()
    assert "ADMITTED: 11 / 28" in log
    assert "GLOBAL ARGMAX (IS-only): bund_02y" in log
    assert "GATE 7 OOS police     FAIL" in log
    assert log.rstrip().endswith("8559fa55ee9a3417 / weights d2d11c92a98683df (must be unchanged)")
    sleeves = [f for f in __import__("os").listdir(DA + "/sleeves") if f.endswith(".csv")]
    assert len(sleeves) == 28, f"expected 28 candidate sleeves, found {len(sleeves)}"
