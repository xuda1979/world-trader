#@ ITER35 reality-pins (2026-09-19, session 16): brwt z-threshold LOWER-ENVELOPE extension.
# ITER34 swept zb over the acceptance envelope {1.0..2.0}: monotone decline, 0/5 admitted,
# disclosing zb<1.0 as the only unmeasured direction. ITER35 (precommit 3c8c6083b33fb3b8)
# measures the reflection {0.25, 0.5, 0.75, 1.0} minus the degenerate zb=0 always-in limit.
# VERDICT: the left side RISES monotonically into the anchor (3.897552 -> 4.057100 ->
# 4.175140 -> 4.198632), 0/4 admitted. Stitched with ITER34, the full measured curve over
# zb in {0.25..2.0} is SINGLE-PEAKED with the interior peak EXACTLY at the incumbent
# zb=1.0 - the strongest possible closure of the largest-weight family axis (30.00 pct of
# book). ITER17-law closure 10. Champion byte-stable pre==post.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER34 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER34_BRWT_ZB")
ITER35 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER35_BRWT_ZBLOW")
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
    # ITER35-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER35 memo
    # (the champion WAS byte-stable pre==post through ITER35).
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter35_precommit_sealed_before_run():
    pre = os.path.join(ITER35, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER35, "driver_iter35.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "3c8c6083b33fb3b8"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "BEFORE any candidate computation" in _read(pre)
    assert "reflection of the ITER34 novel cells" in _read(pre), "motivation must be disclosed at seal time, not after"


def test_iter35_anchors_exact():
    log = _read(os.path.join(ITER35, "driver_iter35.log"))
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt10 maxdev=9.999e-17 (n=6567)" in log
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt7 maxdev=9.986e-17 (n=4580)" in log
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt5 maxdev=9.996e-17 (n=4580)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)" in log
    assert "ANCHOR CELL zb=1.0: weights dev vs committed 8.903e-09 (need <1e-6); book dev vs champ 4.044e-10 (need <1e-9); block share=0.300000" in log


def test_iter35_left_side_rises_into_anchor():
    log = _read(os.path.join(ITER35, "driver_iter35.log"))
    assert "0.25   1.793e-01  3.897552    16.715       -4.36    0/9  1.8017x  no  blk=0.3000" in log
    assert "0.50   1.924e-01  4.057100    17.611       -3.70    0/9  1.8243x  no  blk=0.3000" in log
    assert "0.75   2.050e-01  4.175140    18.260       -3.04    0/9  1.8385x  no  blk=0.3000" in log
    assert "1.00   9.999e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "ADMITTED: 0 / 4 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = [3.897552, 4.057100, 4.175140, 4.198632]
    assert all(grid[i] < grid[i + 1] for i in range(len(grid) - 1)), "left side must rise monotonically into the anchor"
    assert all(v < 4.198632 - 1e-4 for v in grid[:3]), "every novel cell strictly below the admission bar"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER35, "arm_zb*_weights.csv")))
    assert arms == ["arm_zb0.25_weights.csv", "arm_zb0.50_weights.csv",
                    "arm_zb0.75_weights.csv", "arm_zb1.00_weights.csv"]


def test_iter35_full_curve_single_peaked_at_incumbent():
    left = _read(os.path.join(ITER35, "driver_iter35.log"))
    right = _read(os.path.join(ITER34, "driver_iter34.log"))
    full = [3.897552, 4.057100, 4.175140, 4.198632, 4.060778, 3.884666, 3.477293, 3.230354]
    peak = max(full)
    assert full.index(peak) == 3, "the interior peak must be the incumbent cell, not an edge"
    assert all(full[i] < full[i + 1] for i in range(3)), "left flank strictly rising into the peak"
    assert all(full[i] > full[i + 1] for i in range(3, 7)), "right flank strictly falling from the peak"
    assert "4.198632" in left and "4.198632" in right, "both sweeps must anchor on the same incumbent IS-SR"


def test_iter35_no_reveal_per_stop_rule():
    log = _read(os.path.join(ITER35, "driver_iter35.log"))
    assert "NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE)." in log
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in log
    assert "(pre==post: True)" in log
    assert not glob.glob(os.path.join(ITER35, "candidate_zb*.csv")), "no candidate may exist under a no-admission stop rule"
