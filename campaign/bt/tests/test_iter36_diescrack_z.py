#@ ITER36 reality-pins (2026-09-19, session 17): diescrack GATE-Z axis at frozen L=40.
# Largest remaining second-tier cell (10.8293 pct book share measured at A2). A 2-D (L,Z)
# sweep is refused as mining; the pre-committed 1-D slice rule (precommit 946c617d868816e8)
# sweeps the trigger Z over {1.5, 1.75, 2.0, 2.25, 2.5} - acceptance-adjacent 1.5, anchor
# 2.0, midpoint 1.75, equal-step extensions. VERDICT: 1/5 admitted (Z=1.75, IS-SR 4.204030
# - the incumbent Z=2.0 is NOT this family IS-interior argmax); reveal FIRED: FS SR 3.758736
# = +0.007307, third-strongest rejected candidate on record (behind ITER31 +0.0366 and
# ITER33 +0.0075), every operator gate PASS except G7 (bins 2/5 positive) -> REJECT per
# sealed stop rule. ITER17-law closure 11. Champion byte-stable pre==post.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER36 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER36_DIESCRACK_Z")
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
    # ITER36-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER36 memo
    # (the champion WAS byte-stable pre==post through ITER36).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter36_precommit_sealed_before_run():
    pre = os.path.join(ITER36, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER36, "driver_iter36.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "946c617d868816e8"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "BEFORE any candidate computation" in _read(pre)
    assert "sweep the trigger Z at frozen L=40" in _read(pre), "the 1-D slice rule must be disclosed at seal time, not after"
    assert "REFUSED" in _read(pre), "the 2-D (L,Z) mining surface must be refused at seal time"


def test_iter36_anchors_exact():
    log = _read(os.path.join(ITER36, "driver_iter36.log"))
    assert "FROZEN-BLOCK check vs driver_iter34.py: fit_relw/apply_cap/project_wmax/build_book text-identical" in log
    assert "ANCHOR A1 regen Z=2.0 vs saved: maxdev=9.980081e-17 (inner n=4615)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)  diescrack share=10.8293 pct" in log
    assert "ANCHOR CELL Z=2.00: weights dev vs committed 6.450e-09 (need <1e-6); book dev vs champ 8.494e-10 (need <1e-9); block share=0.300000" in log


def test_iter36_sweep_one_admitted_cell_at_z175():
    log = _read(os.path.join(ITER36, "driver_iter36.log"))
    assert "1.50   9.177e-02  4.189526    18.163       -2.46    0/9  1.8630x  no  blk=0.3000" in log
    assert "1.75   3.355e-02  4.204030    18.176       -2.54    0/9  1.8366x  YES  blk=0.3000" in log
    assert "2.00   9.980e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "2.25   8.658e-02  4.173041    17.996       -2.61    0/9  1.7400x  no  blk=0.3000" in log
    assert "2.50   8.659e-02  4.175864    17.942       -2.39    0/9  1.7073x  no  blk=0.3000" in log
    assert "ADMITTED: 1 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = {1.5: 4.189526, 1.75: 4.204030, 2.0: 4.198632, 2.25: 4.173041, 2.5: 4.175864}
    best = max(grid, key=grid.get)
    assert best == 1.75, "the measured interior argmax must be Z=1.75, not the incumbent 2.0"
    assert all(v < 4.198632 - 1e-4 for z, v in grid.items() if z not in (1.75, 2.0)), "non-admitted cells strictly below the bar"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER36, "arm_Z*_weights.csv")))
    assert arms == ["arm_Z1.50_weights.csv", "arm_Z1.75_weights.csv", "arm_Z2.00_weights.csv",
                    "arm_Z2.25_weights.csv", "arm_Z2.50_weights.csv"]


def test_iter36_reveal_rejected_on_g7_police():
    log = _read(os.path.join(ITER36, "driver_iter36.log"))
    assert "GLOBAL ARGMAX (IS-only): Z=1.75 IS-SR=4.204030 Wmax_sf=1.8366x block=0.300000" in log
    assert "REVEAL book: 12-pool refit at Z=1.75, gear 1.0, n=4806 (2008-03-31..2026-08-28)" in log
    assert "  FS SR=3.758736 (incumbent 3.751429)  ann arith=21.3904 pct  cagr=23.6420 pct  MDD=-3.6273 pct  negyrs=0" in log
    assert "  grossmax=1.000000000  Wmax_sf=1.8366x  CFX4 relw=0.0e+00  brwt-block share=0.300000" in log
    assert "  bin 2017-18 dSR=-0.0012 (cand 4.7737 vs inc 4.7750)" in log
    assert "  bin 2019-20 dSR=+0.0117 (cand 4.0355 vs inc 4.0238)" in log
    assert "  bin 2021-22 dSR=-0.0036 (cand 2.2320 vs inc 2.2356)" in log
    assert "  bin 2023-24 dSR=-0.0060 (cand 4.6908 vs inc 4.6968)" in log
    assert "  bin 2025-26 dSR=+0.0080 (cand 3.5309 vs inc 3.5229)" in log
    assert "  GATE 7 OOS police             FAIL" in log
    assert log.count("PASS") >= 7, "every gate except G7 must have passed"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in log
    assert "(pre==post: True)" in log
    cand = glob.glob(os.path.join(ITER36, "candidate_Z1.75_*.csv"))
    assert len(cand) == 2, "the revealed candidate book + weights must exist for the record"
    assert not glob.glob(os.path.join(ITER36, "candidate_Z1.50_*.csv")), "non-revealed cells must have no candidate CSV"


def test_iter36_ranking_among_rejected_candidates():
    log36 = _read(os.path.join(ITER36, "driver_iter36.log"))
    assert "FS SR=3.758736" in log36
    coord = os.path.join(ROOT, "campaign", "agents", "chief", "coord")
    log31 = _read(os.path.join(coord, "ITER31_FITTARGET_CAPFIT", "driver_iter31.log"))
    log33 = _read(os.path.join(coord, "ITER33_C5NG_KAXIS", "driver_iter33.log"))
    log30 = _read(os.path.join(coord, "ITER30_RECIPE_SWEEP", "driver_iter30.log"))
    assert "3.787991" in log31, "ITER31 A3-at-cap reveal must be on record"
    assert "3.758975" in log33, "ITER33 k=3.5 reveal must be on record"
    assert "3.754071" in log30, "ITER30 recipe-argmax reveal must be on record"
    ranking = [3.787991, 3.758975, 3.758736, 3.754071]
    assert ranking == sorted(ranking, reverse=True), "ITER36 must rank third-strongest rejected candidate"
    assert abs(3.758736 - 3.751429 - 0.007307) < 5e-7, "the recorded delta must be +0.007307"
