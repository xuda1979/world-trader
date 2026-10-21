"""ITER25 reality-pins (2026-09-19, session #7): A5_r7_credit re-adjudication closed
honest-negative at the IS concentration filter. The fit EARNED the IS-SR bar (4.2575 >
4.198632) and the pool's LARGEST allocation ever (19.03%), but Wmax 2.4745x > 2.0x ->
NO-ADMISSION -> no reveal (sealed stop rule). Pins assert on recorded artifacts (log +
CSV bytes), never on a pipeline exit code."""
import hashlib
import os

import pandas as pd
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER25 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER25_CREDIT_READJ")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER25-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER25 memo.
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter25_precommit_sealed_and_tamper_evident():
    pre = os.path.join(ITER25, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER25, "driver_2026-09-19.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "d176f7cb8f2f11f5"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    with open(logf) as fh:
        head = fh.read(400)
    assert "sealed 02:44 BEFORE this run" in head
    assert "precommit d176f7cb8f2f11f5" in head


def test_iter25_fit_earned_is_bar_and_largest_allocation():
    w = pd.read_csv(os.path.join(ITER25, "candidate_A5r7credit_weights.csv"), index_col=0).iloc[:, 0]
    assert abs(float(w["A5r7credit"]) - 0.19034) < 5e-5
    blk = float(w[["brwt10", "brwt7", "brwt5"]].sum())
    assert abs(blk - 0.30) < 1e-6  # brwt cap bit exactly
    assert float(w["CFX4"]) == 0.0


def test_iter25_wmax_blocks_admission():
    w = pd.read_csv(os.path.join(ITER25, "candidate_A5r7credit_weights.csv"), index_col=0).iloc[:, 0]
    wmax = float(w.max()) * 13.0
    assert abs(wmax - 2.4745) < 1e-3
    assert wmax > 2.0  # the concentration invariant binds: this IS the rejection
    with open(os.path.join(ITER25, "driver_2026-09-19.log")) as fh:
        log = fh.read()
    assert "ANCHOR incumbent IS-SR=4.198632" in log
    assert "ADMITTED: NO (filters False, IS-SR bar True)" in log
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per pre-commit)" in log
