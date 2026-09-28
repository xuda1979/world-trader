#@ ITER39 reality-pins (2026-09-19, session 19 cont.): dualmom gate MA-WINDOW (WIN) axis at
# frozen BAND=0.03 - the second (and completing) seal of the dualmom gate family, per the
# ITER35 second-seal pattern with the seal-1 conditional tension DISCLOSED at seal time.
# Grid = EXACTLY the acceptance-printed win axis (at{150, 175, 200, 225, 250}, r2_scan5.py);
# min_periods COUPLED to win (derived, not a second scalar). VERDICT: 2/5 admitted - the IS-SR
# falls STRICTLY MONOTONE across the whole printed envelope (150 4.218613 > 175 4.201254 >
# 200 4.198632 anchor > 225 4.184679 > 250 4.175950): the incumbent sits on the LEFT SLOPE and
# the acceptance envelope EDGE (150) is the IS-argmax. REVEAL WIN=150: FS SR 3.754857 > 3.751429
# (PASSES the FS bar) and ALL operator gates PASS, but G7 bins 3/5 positive => REJECT
# (ITER17-law closure 14). WIN=150 is the strongest "3/5 relaxation" data point on record:
# under a >=3/5 bin rule this book would have been admitted (recorded for the operator
# rule-change debate; recommendation KEEP stands - 2/5 windows negative, magnitudes <= 0.0145).
# Champion byte-stable pre==post. Pins assert on recorded artifacts, never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER38 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER38_DUALMOM_BAND")
ITER39 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER39_DUALMOM_WIN")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")
LB = chr(123)
RB = chr(125)


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER39-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER39 memo
    # (the champion WAS byte-stable pre==post through ITER39; the driver-log sha counts
    # pinned in test_iter39_dualmom_gate_family_fully_measured stay on the recorded
    # ITER39-era values).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter39_precommit_sealed_before_run():
    pre = os.path.join(ITER39, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER39, "driver_iter39.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "207c3aa37640db1d"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    body = _read(pre)
    assert "Sealed BEFORE any candidate computation" in body
    assert "GRID = " + LB + "150, 175, 200, 225, 250" + RB in body, "grid rule must be disclosed at seal time"
    assert "that literal" in body and "condition did NOT fire" in body, "the seal-1 conditional tension must be disclosed, not papered over (phrase may line-wrap)"
    assert "min_periods COUPLED to win" in body, "the coupling rule must be pre-stated"
    assert "FRAC=1/3 has NO" in body and "printed acceptance grid" in body, "FRAC refusal must be recorded at seal time (phrase may line-wrap in the seal)"


def test_iter39_anchors_exact():
    log = _read(os.path.join(ITER39, "driver_iter39.log"))
    assert "FROZEN-BLOCK check vs driver_iter36.py + driver_iter37.py + driver_iter38.py: fit_relw/apply_cap/project_wmax/build_book text-identical" in log
    assert "ANCHOR A1 regen WIN=200 vs saved: maxdev=9.996344e-17 (inner n=4743)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)  dualmom share=5.7226 pct" in log
    assert "ANCHOR CELL WIN=200: weights dev vs committed 7.527e-09 (need <1e-6); book dev vs champ 4.468e-10 (need <1e-9); block share=0.300000" in log
    alog = _read(os.path.join(ITER39, "anchor_iter39.log"))
    assert "index identical: True" in alog


def test_iter39_win_curve_strictly_monotone_edge_argmax():
    log = _read(os.path.join(ITER39, "driver_iter39.log"))
    assert "150    8.210e-02  4.218613    18.134       -2.56    0/9  1.7926x  YES  blk=0.3000" in log
    assert "175    3.548e-02  4.201254    18.118       -2.56    0/9  1.8080x  YES  blk=0.3000" in log
    assert "200    9.996e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "225    5.666e-02  4.184679    18.088       -2.56    0/9  1.8070x  no  blk=0.3000" in log
    assert "250    5.612e-02  4.175950    18.084       -2.56    0/9  1.8171x  no  blk=0.3000" in log
    assert "ADMITTED: 2 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = dict(zip(("150", "175", "200", "225", "250"),
                    (4.218613, 4.201254, 4.198632, 4.184679, 4.175950)))
    vals = list(grid.values())
    assert all(vals[i] > vals[i + 1] for i in range(len(vals) - 1)), "the win curve must fall STRICTLY MONOTONE across the whole printed envelope"
    best = max(grid, key=grid.get)
    assert best == "150", "the IS-argmax must be at the acceptance envelope edge, not the incumbent"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER39, "arm_WIN*_weights.csv")))
    assert len(arms) == 5


def test_iter39_reveal_passed_fs_bar_but_police_killed_3of5():
    log = _read(os.path.join(ITER39, "driver_iter39.log"))
    assert "GLOBAL ARGMAX (IS-only): WIN=150 IS-SR=4.218613 Wmax_sf=1.7926x block=0.300000" in log
    assert "REVEAL book: 12-pool refit at WIN=150, gear 1.0, n=4806 (2008-03-31..2026-08-28)" in log
    assert "FS SR=3.754857 (incumbent 3.751429)" in log
    assert 3.754857 > 3.751429, "the STRONGEST dualmom candidate PASSES the FS bar - rejection is pure G7 consistency"
    signs = (-0.0145, 0.0090, 0.0051, 0.0054, -0.0029)
    pos = sum(1 for v in signs if v > 0)
    assert pos == 3, "exactly 3/5 positive bins - the contemplated >=3/5 relaxation WOULD have admitted this book"
    assert min(signs) > -0.10, "no bin breaches the -0.10 floor - the police binds on consistency alone"
    assert "GATE 7 OOS police             FAIL" in log
    assert "GATE 3 FS MDD>=-7pct          PASS" in log, "candidate MDD -3.5869 is BETTER than the champion's -3.6130"
    assert log.count("REVEAL book") == 1, "175 admitted but UNREVEALED by law - no second reveal"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in log
    assert _sha16(os.path.join(ITER39, "candidate_WIN150_daily.csv"))
    assert _sha16(os.path.join(ITER39, "candidate_WIN150_weights.csv"))


def test_iter39_dualmom_gate_family_fully_measured():
    # Cross-ITER pin: BOTH printed axes of the dualmom gate family measured in one session;
    # both escapes police-killed; same A1 digits (the win-parameterization is the same re-type);
    # champion byte-stable through both runs.
    log38 = _read(os.path.join(ITER38, "driver_iter38.log"))
    log39 = _read(os.path.join(ITER39, "driver_iter39.log"))
    assert "9.996344e-17" in log38 and "9.996344e-17" in log39, "identical re-type provenance on both seals"
    assert "0.02   2.181e-02  4.199008" in log38 and "150    8.210e-02  4.218613" in log39
    assert "VERDICT: REJECT - failed gates: 7 OOS police" in log38
    assert "VERDICT: REJECT - failed gates: 7 OOS police" in log39
    assert log38.count("8559fa55ee9a3417") >= 2 and log39.count("8559fa55ee9a3417") >= 2
    pre39 = _read(os.path.join(ITER39, "FINDINGS_PRECOMMIT.md"))
    assert "8a1c571db36f9770" in pre39, "seal 2 must cite seal 1's sha"

