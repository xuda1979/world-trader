"""ITER27/ITER28 reality-pins (2026-09-19, session #10): census-remainder closure.

ITER27 sealed the two cells the 2026-09-19 census had closed WITHOUT measurement
(29 cboe non-vol capital-real ETFs + the nokcarry two-leg) but its Wmax filter was
miscalibrated (max_share x 13 <= 2.0 while the covered pool is 11/12 - the incumbent
committed fit itself violates that form). ITER28 repaired the filter to the recorded
scale-free invariant (max_share x k_covered <= 2.0), re-measured the same frozen set
(2/30 admitted: xly real, xlf a relw-0 solver-jitter admission), and fired xly's first
reveal: FS SR 3.750133 < 3.751429, OOS bins 2/5 positive -> G7 FAIL -> REJECT
(ITER17 law kill #5). Champion byte-stable throughout.

Pins assert on recorded artifacts (log lines + file bytes), never on a pipeline
exit code, per house rule.
"""
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER27 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER27_CENSUS_REMAINDER")
ITER28 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER28_CENSUSREMAINDER_FIX")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER27/28-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved
    # byte-exact in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the
    # ITER27/ITER28 memos (the champion WAS byte-stable through both iterations).
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter27_as_sealed_honest_negative_and_precommit():
    pre = os.path.join(ITER27, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER27, "driver_iter27.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "ccd882e6391f3742"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    log = _read(logf)
    assert "ADMITTED: 0 / 30" in log
    assert "NO candidate admitted -> HONEST NEGATIVE, no reveal" in log
    assert "ANCHOR incumbent IS-SR=4.198632" in log
    assert log.count("8559fa55ee9a3417") >= 2  # pre and post champion sha lines


def test_iter27_defect_disclosure_on_the_record():
    find = _read(os.path.join(ITER27, "FINDINGS.md"))
    assert "DEFECT DISCLOSED" in find
    assert "x13" in find and "k_covered" in find
    assert "xly_etf" in find


def test_iter28_repair_precommit_sealed_before_run():
    pre = os.path.join(ITER28, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER28, "driver_iter28.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "9c1f22cba582364a"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)


def test_iter28_repair_table_and_argmax():
    log = _read(os.path.join(ITER28, "driver_iter28.log"))
    assert "ADMITTED: 2 / 30" in log
    assert "GLOBAL ARGMAX (IS-only): xly_etf  IS-SR=4.200683" in log
    assert "ANCHOR incumbent IS-SR=4.198632" in log
    assert "NOK unit gate: tail60 ann=4.3412%" in log


def test_iter28_reveal_rejected_on_oos_police():
    log = _read(os.path.join(ITER28, "driver_iter28.log"))
    assert "REVEAL book: 13-pool + xly_etf at gear 1.0, n=4813" in log
    assert "FS SR=3.750133" in log and "3.751429" in log
    assert "GATE 7 OOS police     FAIL" in log
    assert "VERDICT: REJECT -- honest negative, no second reveal" in log
    # operator constraints all passed on the rejected candidate too
    for gate in ("GATE 1 FS ann>=20%    PASS", "GATE 2 gross<=1.6     PASS",
                 "GATE 4 0 FS neg yrs   PASS", "GATE 6 Wmax<=2.0x     PASS"):
        assert gate in log
