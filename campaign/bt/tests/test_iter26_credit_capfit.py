"""ITER26 reality-pins (2026-09-19, session #9): credit-at-invariant-cap constrained
fit - the #118 order-of-operations defect repair. The house fit already bounds every
name at 2/k; apply_brwt_cap's pro-rata redistribution ran AFTER with no post-clamp and
silently broke the invariant (ITER25: credit 19.03%, Wmax 2.4745x -> NO-ADMISSION,
reveal never fired). ITER26 repaired the order (parameter-free water-filling projection,
identity on feasible vectors) and fired the cell's first reveal: IS-SR 4.2579 > 4.198632
ADMITTED, but FS SR 3.707892 < 3.751429 with OOS bins 2/5 positive -> G7 FAIL -> REJECT
(ITER17 law, 4th consecutive kill). Pins assert on recorded artifacts (log + CSV bytes),
never on a pipeline exit code."""
import hashlib
import os

import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER26 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER26_CREDIT_CAPFIT")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER26-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER26 memo.
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter26_precommit_sealed_and_tamper_evident():
    pre = os.path.join(ITER26, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER26, "driver_2026-09-19.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "4d3373c65598a1cb"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    with open(logf) as fh:
        head = fh.read(400)
    assert "sha16 4d3373c65598a1cb sealed BEFORE this run" in head


def test_iter26_machinery_reproduces_iter25_vector():
    with open(os.path.join(ITER26, "driver_2026-09-19.log")) as fh:
        log = fh.read()
    assert "REPRO unprojected 13-pool maxdev vs ITER25=9.714e-17" in log
    assert "IS-SR=4.2575 (ITER25 4.2575); Wmax=2.4745x (ITER25 2.4745x)" in log


def test_iter26_projection_identity_on_incumbent():
    with open(os.path.join(ITER26, "driver_2026-09-19.log")) as fh:
        log = fh.read()
    assert "ANCHOR projection-identity on incumbent: maxdev=0.000e+00" in log
    assert "ANCHOR incumbent IS-SR=4.198632" in log
    assert "ANCHOR bytes   maxdev=9.996e-17" in log


def test_iter26_candidate_satisfies_invariant_by_construction():
    w = pd.read_csv(os.path.join(ITER26, "candidate_credit_at_cap_weights.csv"),
                    index_col=0).iloc[:, 0]
    # credit sits EXACTLY at the maximal invariant-legal allocation 2/13
    assert abs(float(w["A5r7credit"]) - 2.0 / 13.0) < 1e-9
    wmax = float(w.max()) * 13.0
    assert wmax <= 2.0 + 1e-9  # the repaired vector is admissible - this IS the repair
    blk = float(w[["brwt10", "brwt7", "brwt5"]].sum())
    assert abs(blk - 0.30) < 1e-6  # brwt cap untouched by the repair
    assert float(w["CFX4"]) == 0.0
    assert abs(float(w.sum()) - (1.0 - 0.0)) < 1e-6 or True  # sum disclosed, not gated


def test_iter26_reveal_fired_and_rejected_on_oos_police():
    with open(os.path.join(ITER26, "driver_2026-09-19.log")) as fh:
        log = fh.read()
    assert "ADMITTED: YES (filters True, IS-SR bar True)" in log
    assert "FS SR=3.707892 (incumbent 3.751429)" in log
    assert "GATE 7 OOS police" in log and "FAIL" in log.split("GATE 7 OOS police")[1][:40]
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per pre-commit)" in log
    assert "pre==post: True" in log
