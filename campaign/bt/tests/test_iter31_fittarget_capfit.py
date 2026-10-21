### ITER31 reality-pins (2026-09-19, session '13): covariance-TARGET arms AT the
# invariant cap. #121 closed the estimator-target axis by inadmissibility (A3/A4 sat
# past the Wmax wall); this iteration applied the #119 repair precedent (water-fill to
# 2/k_covered, k=11 per the #120 canonical convention) and fired the FIRST
# estimator-family reveal. VERDICT: both arms admitted at the cap (projection cost
# 0.0001/0.0013 IS-SR - pure shadow-pricing; REPRO vs ITER29 saved arms 6.9e-17);
# argmax A3 reveal FS SR 3.787991 (+0.0366 over incumbent, ALL operator gates pass)
# but the 5-bin OOS police reads 2/5 positive (gains front-loaded 2017-20, erosion
# 2021-26) => G7 FAIL => REJECT per sealed stop rule. Strongest rejected candidate on
# record; champion byte-stable.

# Pins assert on recorded artifacts (log lines + file bytes), never on a pipeline
# exit code, per house rule.
###
import hashlib
import glob
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER31 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER31_FITTARGET_CAPFIT")
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
    # ITER31-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER31 memo
    # (the champion WAS byte-stable through ITER31).
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter31_precommit_sealed_before_run():
    pre = os.path.join(ITER31, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER31, "driver_iter31.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "70c776c7f82a96c8"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "SEALED BEFORE ANY ITER31 CANDIDATE COMPUTATION" in _read(pre)


def test_iter31_anchors_exact():
    log = _read(os.path.join(ITER31, "driver_iter31.log"))
    assert "ANCHOR projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR incumbent Wmax_sf(x11)=1.8115x (feasible under corrected invariant)" in log
    assert "ANCHOR incumbent IS-SR=4.198632 (continuity 4.198632)" in log
    assert "ANCHOR fit rows=1809 k_covered=11" in log


def test_iter31_arm_table_structure():
    log = _read(os.path.join(ITER31, "driver_iter31.log"))
    # A3 constvar at cap: unprojected 4.2444 -> projected 4.2443 at Wmax_sf 2.0000x
    assert "A3   constvar     0.7000     4.2444      4.2443" in log
    assert "2.0000x  YES" in log
    assert "REPRO vs ITER29 saved arm: maxdev=6.939e-17 (need <1e-9); moved mass 0.017560" in log
    # A4 diag-LW04 at cap: unprojected 4.2274 -> projected 4.2261 at Wmax_sf 2.0000x
    assert "A4   diag-lw04    0.0293     4.2274      4.2261" in log
    assert "REPRO vs ITER29 saved arm: maxdev=6.939e-17 (need <1e-9); moved mass 0.015211" in log
    assert "ADMITTED: 2 / 2 (jitter tolerance 1e-4 on the IS bar)" in log


def test_iter31_argmax_reveal_oos_rejection():
    log = _read(os.path.join(ITER31, "driver_iter31.log"))
    assert "GLOBAL ARGMAX (IS-only): A3 (constvar, s=0.7000) IS-SR=4.244277 Wmax_sf=2.0000x" in log
    assert "FS SR=3.787991 (incumbent 3.751429)  ann arith=21.4716%  cagr=23.7438%  MDD=-3.8237%  negyrs=0" in log
    # the five OOS police bins: +, +, -, -, - = 2/5 positive (G7 needs >= 4/5)
    assert "bin 2017-18 dSR=+0.0452" in log
    assert "bin 2019-20 dSR=+0.0336" in log
    assert "bin 2021-22 dSR=-0.0031" in log
    assert "bin 2023-24 dSR=-0.0788" in log
    assert "bin 2025-26 dSR=-0.0179" in log
    assert "GATE 7 OOS police             FAIL" in log
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per pre-commit)" in log
    assert "(pre==post: True)" in log
    assert glob.glob(os.path.join(ITER31, "candidate_A3_atcap_daily.csv"))


def test_iter31_atcap_weights_satisfy_invariant():
    import pandas as pd
    for arm in ("A3", "A4"):
        w = pd.read_csv(os.path.join(ITER31, "arm_" + arm + "_atcap_weights.csv"), index_col=0).iloc[:, 0]
        assert abs(float(w.sum()) - 1.0) < 1e-12
        assert float(w["CFX4"]) == 0.0
        assert float(w.max()) * 11.0 <= 2.0 + 1e-9
        assert abs(float(w.max()) * 11.0 - 2.0) < 1e-6  # the cap binds (shadow-priced cell)
        blk = float(w[["brwt10", "brwt7", "brwt5"]].sum())
        assert blk <= 0.30 + 1e-9
