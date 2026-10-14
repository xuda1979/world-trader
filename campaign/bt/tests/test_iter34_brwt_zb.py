#@ ITER34 reality-pins (2026-09-19, session 16): the brwt-family z-threshold scalar zb.
# ITER33 closed the signal-parameter axis for the C5ng family (k=2.5 freeze OOS-vindicated,
# G7 kill of the IS-better cell). ITER34 sweeps the ONE frozen scalar of the LARGEST
# committed exposure: zb=1.0 in the brwt generator (Brent-WTI log-spread z mean-reversion;
# brwt10/brwt7/brwt5 = 30.0000 pct of book, sitting EXACTLY at the 0.30 brwt-block share
# cap); zb in {1.0, 1.25, 1.5, 1.75, 2.0} SHARED across all three variants per the sealed
# precommit b9b9539c7dbe41ef (acceptance-print points {1.0, 1.5, 2.0} plus midpoints).
# VERDICT: IS-SR FALLS MONOTONICALLY from the incumbent freeze (4.198632 -> 3.230354 over
# the envelope; every interior cell strictly below the bar) => 0/5 admitted => HONEST
# NEGATIVE, no reveal, per the sealed stop rule. Third closure shape in the signal-
# parameter class (DUR interior-max; k OOS-vindicated freeze; zb monotone-from-freeze):
# IS itself certifies the freeze - no police needed. Champion byte-stable pre==post.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER34 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER34_BRWT_ZB")
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
    # ITER34-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER34 memo
    # (the champion WAS byte-stable pre==post through ITER34).
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter34_precommit_sealed_before_run():
    pre = os.path.join(ITER34, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER34, "driver_iter34.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "b9b9539c7dbe41ef"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "BEFORE any candidate computation" in _read(pre)


def test_iter34_anchors_exact():
    log = _read(os.path.join(ITER34, "driver_iter34.log"))
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt10 maxdev=9.999e-17 (n=6567)" in log
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt7 maxdev=9.986e-17 (n=4580)" in log
    assert "ANCHOR A1 regen zb=1.0 vs saved: brwt5 maxdev=9.996e-17 (n=4580)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)" in log
    assert "ANCHOR CELL zb=1.0: weights dev vs committed 8.903e-09 (need <1e-6); book dev vs champ 4.044e-10 (need <1e-9); block share=0.300000" in log


def test_iter34_sweep_monotone_decline_no_admission():
    log = _read(os.path.join(ITER34, "driver_iter34.log"))
    assert "1.00   9.999e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "1.25   1.290e-01  4.060778    16.492       -3.26    0/9  1.7859x  no  blk=0.3000" in log
    assert "1.50   1.300e-01  3.884666    15.578       -2.66    0/9  1.7584x  no  blk=0.3000" in log
    assert "1.75   1.300e-01  3.477293    13.046       -2.18    0/9  1.7148x  no  blk=0.3000" in log
    assert "2.00   1.873e-01  3.230354    11.812       -2.16    0/9  1.9867x  no  blk=0.2819" in log
    assert "ADMITTED: 0 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER34, "arm_zb*_weights.csv")))
    assert arms == ["arm_zb1.00_weights.csv", "arm_zb1.25_weights.csv",
                    "arm_zb1.50_weights.csv", "arm_zb1.75_weights.csv",
                    "arm_zb2.00_weights.csv"]


def test_iter34_incumbent_edge_optimal_on_envelope():
    log = _read(os.path.join(ITER34, "driver_iter34.log"))
    grid = [4.198632, 4.060778, 3.884666, 3.477293, 3.230354]
    assert all(grid[i] > grid[i + 1] for i in range(len(grid) - 1)), "IS-SR must fall monotonically in zb over the measured envelope"
    assert all(v < 4.198632 - 1e-4 for v in grid[1:]), "every novel cell strictly below the admission bar - the freeze needs no police"


def test_iter34_no_reveal_per_stop_rule():
    log = _read(os.path.join(ITER34, "driver_iter34.log"))
    assert "NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE)." in log
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in log
    assert "(pre==post: True)" in log
    assert not glob.glob(os.path.join(ITER34, "candidate_zb*.csv")), "no candidate may exist under a no-admission stop rule"
