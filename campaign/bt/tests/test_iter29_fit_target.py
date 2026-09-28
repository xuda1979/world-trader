"""ITER29 reality-pins (2026-09-19, session #11): weight-fit covariance-TARGET family.

The shrink intensity was closed (ITER22/23); the shrink TARGET form was this
iteration's frozen family (constcorr / singleindex / constvar @ s=0.70 + diag-LW04
optimal intensity). VERDICT: ADMITTED 0/4 — honest negative, no reveal, stop rule
honored; champion byte-stable. Structure pinned: every bar-beating arm sits past the
Wmax 2.0x wall (A3 2.0966x, A4 2.0837x); the only in-wall arm (A2 singleindex)
reproduces the COMMITTED champion weights to 1.5e-6 — an independent-estimator
cross-validation of the incumbent fit.

Pins assert on recorded artifacts (log lines + file bytes), never on a pipeline
exit code, per house rule.
"""
import hashlib
import glob
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER29 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER29_FIT_TARGET")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_champion_bytes_unchanged_through_iter29():
    # Re-anchored 2026-09-19 (ITER43 adoption): the live pair legitimately changed to
    # e67446186e269b88 / bde8612d0b295068; the ITER29-era bytes are preserved byte-exact
    # in the ITER43 prior_champion_backup pair (8559fa55ee9a3417 / d2d11c92a98683df).
    bk = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER43_A5R2_VT",
                      "prior_champion_backup")
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"
    assert _sha16(os.path.join(bk, "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")) == "8559fa55ee9a3417"
    assert _sha16(os.path.join(bk, "RAWEW13v2_IS_SR_weights.csv")) == "d2d11c92a98683df"


def test_iter29_precommit_sealed_before_run():
    pre = os.path.join(ITER29, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER29, "driver_iter29.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "040d6db10788b7f8"  # includes Amendment 1
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "AMENDMENT 1 (pre-run, BEFORE any variant computation" in _read(pre)


def test_iter29_anchors_exact():
    log = _read(os.path.join(ITER29, "driver_iter29.log"))
    assert "ANCHOR weights maxdev=8.327e-17" in log
    assert "ANCHOR bytes   maxdev=9.996e-17 (need <1e-12)  n=4806" in log
    assert "ANCHOR incumbent IS-SR=4.198632 (continuity 4.198632)" in log
    assert "12-pool fit rows=1809 k_covered=11" in log


def test_iter29_arm_table_structure():
    log = _read(os.path.join(ITER29, "driver_iter29.log"))
    # A1 constcorr: double-dead (below bar AND past the wall)
    assert "A1   constcorr      0.7000    0.23163    4.1658" in log
    assert "2.5479x" in log
    # A2 singleindex: equality plateau at the bar, INSIDE the wall
    assert "A2   singleindex    0.7000    0.16468    4.1986" in log
    assert "1.8115x" in log
    # A3 constvar: best arm, bar-beating, BLOCKED by the invariant
    assert "A3   constvar       0.7000    0.19060    4.2444" in log
    assert "2.0966x" in log
    # A4 diag-LW04: data-driven intensity 2.93 pct, bar-beating, BLOCKED by the invariant
    assert "A4   diag-lw04      0.0293    0.18942    4.2274" in log
    assert "2.0837x" in log


def test_iter29_honest_negative_no_reveal():
    log = _read(os.path.join(ITER29, "driver_iter29.log"))
    assert "ADMITTED: 0 / 4" in log
    assert "NO arm admitted -> HONEST NEGATIVE, no reveal (per pre-commit STOP RULE)." in log
    assert "REVEAL book" not in log  # the reveal never fired
    assert not glob.glob(os.path.join(ITER29, "candidate_*.csv"))


def test_iter29_a2_fixed_point_cross_validates_committed_weights():
    import pandas as pd
    # Re-anchored 2026-09-19 (ITER43): the cross-validation target is the champion of the
    # ITER29 era -- the preserved prior_champion_backup weights (d2d11c92a98683df) -- not
    # the live ITER43 weights.
    a2 = pd.read_csv(os.path.join(ITER29, "arm_A2_weights.csv"), index_col=0).iloc[:, 0]
    com = pd.read_csv(os.path.join(ROOT, "campaign", "agents", "chief", "coord",
                                   "ITER43_A5R2_VT", "prior_champion_backup",
                                   "RAWEW13v2_IS_SR_weights.csv"), index_col=0).iloc[:, 0]
    j = pd.concat([a2.rename("a2"), com.rename("com")], axis=1).fillna(0.0)
    assert float((j["a2"] - j["com"]).abs().max()) < 1e-5
