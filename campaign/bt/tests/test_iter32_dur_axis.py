### ITER32 reality-pins (2026-09-19, session 14): the DUR signal-parameter axis.
# The a6r7 generator duration coefficient DUR=1.9 was FROZEN by the ITER30 recipe
# sweep (which measured only the trading recipe K/CAD/VT/CAP). This iteration swept
# it: DUR in {1.40, 1.65, 1.90, 2.15, 2.40}, everything else byte-frozen per the
# sealed precommit 8ebb2c3da5faf91f. VERDICT: honest negative - every novel cell is
# IS-lowering (best novel 4.197999 at DUR=2.15 vs bar 4.198632 + 1e-4 jitter); the
# incumbent coefficient is the IS argmax of its own one-parameter family. FOURTH
# independent plateau confirmation; no reveal consumed; champion byte-stable.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
###

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER32 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER32_DUR_AXIS")
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
    # ITER32-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER32 memo
    # (the champion WAS byte-stable through ITER32).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter32_precommit_sealed_before_run():
    pre = os.path.join(ITER32, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER32, "driver_iter32.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "8ebb2c3da5faf91f"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "SEALED BEFORE ANY ITER32 CANDIDATE COMPUTATION" in _read(pre)


def test_iter32_anchors_exact():
    log = _read(os.path.join(ITER32, "driver_iter32.log"))
    assert "ANCHOR A2 legacy generator DUR=1.90 vs saved: maxdev=9.975e-17 (need <1e-12) inner_n=9168 gen_n=9168 saved_n=9168" in log
    assert "ANCHOR A3 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A3 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A3 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A3 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A3 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)" in log


def test_iter32_cell_table_full_grid_below_bar():
    log = _read(os.path.join(ITER32, "driver_iter32.log"))
    assert "1.40   1.350e-02  4.192924    17.859       -2.55    0/9  1.6129x  no" in log
    assert "1.65   1.149e-02  4.196927    18.004       -2.56    0/9  1.7204x  no" in log
    assert "1.90   9.975e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)" in log
    assert "2.15   1.351e-02  4.197999    18.178       -2.56    0/9  1.8551x  no" in log
    assert "2.40   2.612e-02  4.197272    18.226       -2.56    0/9  1.8941x  no" in log
    assert "ANCHOR CELL DUR=1.90: weights dev vs committed 5.483e-09 (need <1e-6); book dev vs champ 2.477e-10 (need <1e-9)" in log


def test_iter32_no_admission_no_reveal():
    log = _read(os.path.join(ITER32, "driver_iter32.log"))
    assert "ADMITTED: 0 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    assert "NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE)." in log
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in log
    assert "(pre==post: True)" in log
    assert "GLOBAL ARGMAX" not in log
    assert "REVEAL book" not in log
    assert "GATE " not in log
    assert not glob.glob(os.path.join(ITER32, "candidate_*_daily.csv"))


def test_iter32_incumbent_is_grid_argmax_and_arms_recorded():
    log = _read(os.path.join(ITER32, "driver_iter32.log"))
    anchor_sr = 4.198632
    for novel in ("4.192924", "4.196927", "4.197999", "4.197272"):
        assert float(novel) < anchor_sr - 1e-4, "novel cell would have been admitted"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER32, "arm_dur*_weights.csv")))
    assert arms == ["arm_dur1.40_weights.csv", "arm_dur1.65_weights.csv",
                    "arm_dur1.90_weights.csv", "arm_dur2.15_weights.csv",
                    "arm_dur2.40_weights.csv"]
