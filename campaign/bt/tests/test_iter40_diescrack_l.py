#@ ITER40 reality-pins (2026-09-19, session 20): diescrack GATE-L axis at frozen Z=2.0 -
# the OTHER printed axis of the 36-refused 2-D surface, sealed under the 38/39 two-slice
# family standard (precommit f72f8a8b6466a059). Grid (15, 27, 40, 53) = printed 15/40 +
# floor-midpoint 27 + one equal-step extension 53 (66 truncated by the coverage law,
# disclosed pre-seal). VERDICT: 1/4 admitted (L=27, IS-SR 4.206566 - interior peak, the
# incumbent L=40 is NOT this family IS-interior argmax); reveal FIRED: FS SR 3.767511 =
# +0.016082, SECOND-strongest rejected candidate on record (behind only ITER31 +0.0366),
# every operator gate PASS (cagr 23.7646 ABOVE the champion, gross 1.0, MDD -3.7668,
# 0 negy, CFX4 0, Wmax 1.9482x, G8 0) except G7 (bins 2/5 positive, min -0.0613) -> REJECT
# per sealed stop rule. ITER17-law closure 15; diescrack family now measured-closed on
# BOTH printed axes. Champion byte-stable pre==post.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER40 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER40_DIESCRACK_L")
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
    # ITER40-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER40 memo
    # (the champion WAS byte-stable pre==post through ITER40).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter40_precommit_sealed_before_run():
    pre = os.path.join(ITER40, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER40, "driver_iter40.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "f72f8a8b6466a059"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "BEFORE any candidate computation" in _read(pre)
    assert "L in (15, 27, 40, 53) at frozen gate Z=2.0" in _read(pre), "the grid must be pre-committed at seal time, not after"
    assert "The 2-D surface stays REFUSED" in _read(pre), "the 2-D (L,Z) mining surface must be refused at seal time"


def test_iter40_anchors_exact():
    log = _read(os.path.join(ITER40, "driver_iter40.log"))
    assert "FROZEN-BLOCK check vs driver_iter36.py: fit_relw/apply_cap/project_wmax/build_book text-identical" in log
    assert "ANCHOR A1 regen L=40 Z=2.0 vs saved: maxdev=9.980081e-17 (inner n=4615)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)  diescrack share=10.8293 pct" in log
    assert "ANCHOR CELL L=40: weights dev vs committed 6.450e-09 (need <1e-6); book dev vs champ 8.494e-10 (need <1e-9); block share=0.300000" in log


def test_iter40_sweep_one_admitted_cell_at_l27():
    log = _read(os.path.join(ITER40, "driver_iter40.log"))
    assert "15     8.661e-02  4.182945    18.261       -2.43    0/9  1.9028x  no  blk=0.3000" in log
    assert "27     4.818e-02  4.206566    18.278       -2.34    0/9  1.9482x  YES  blk=0.3000" in log
    assert "40     9.980e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "53     4.369e-02  4.197074    18.174       -2.52    0/9  1.8621x  no  blk=0.3000" in log
    assert "ADMITTED: 1 / 4 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = {15: 4.182945, 27: 4.206566, 40: 4.198632, 53: 4.197074}
    best = max(grid, key=grid.get)
    assert best == 27, "the measured interior argmax must be L=27, not the incumbent 40"
    assert all(v < 4.198632 - 1e-4 for l, v in grid.items() if l not in (27, 40)), "non-admitted cells strictly below the bar"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER40, "arm_L*_weights.csv")))
    assert arms == ["arm_L15_weights.csv", "arm_L27_weights.csv", "arm_L40_weights.csv",
                    "arm_L53_weights.csv"]


def test_iter40_reveal_rejected_on_g7_police():
    log = _read(os.path.join(ITER40, "driver_iter40.log"))
    assert "GLOBAL ARGMAX (IS-only): L=27 IS-SR=4.206566 Wmax_sf=1.9482x block=0.300000" in log
    assert "REVEAL book: 12-pool refit at L=27, gear 1.0, n=4806 (2008-03-31..2026-08-28)" in log
    assert "  FS SR=3.767511 (incumbent 3.751429)  ann arith=21.4904 pct  cagr=23.7646 pct  MDD=-3.7668 pct  negyrs=0" in log
    assert "  grossmax=1.000000000  Wmax_sf=1.9482x  CFX4 relw=0.0e+00  brwt-block share=0.300000" in log
    assert "  bin 2017-18 dSR=-0.0010 (cand 4.7740 vs inc 4.7750)" in log
    assert "  bin 2019-20 dSR=+0.0402 (cand 4.0640 vs inc 4.0238)" in log
    assert "  bin 2021-22 dSR=-0.0339 (cand 2.2017 vs inc 2.2356)" in log
    assert "  bin 2023-24 dSR=-0.0613 (cand 4.6355 vs inc 4.6968)" in log
    assert "  bin 2025-26 dSR=+0.0157 (cand 3.5385 vs inc 3.5229)" in log
    assert "  GATE 7 OOS police             FAIL" in log
    assert log.count("PASS") >= 7, "every gate except G7 must have passed"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in log
    assert "(pre==post: True)" in log
    cand = glob.glob(os.path.join(ITER40, "candidate_L27_*.csv"))
    assert len(cand) == 2, "the revealed candidate book + weights must exist for the record"
    assert not glob.glob(os.path.join(ITER40, "candidate_L15_*.csv")), "non-revealed cells must have no candidate CSV"
    assert not glob.glob(os.path.join(ITER40, "candidate_L53_*.csv")), "non-revealed cells must have no candidate CSV"


def test_iter40_ranking_among_rejected_candidates():
    log40 = _read(os.path.join(ITER40, "driver_iter40.log"))
    assert "FS SR=3.767511" in log40
    coord = os.path.join(ROOT, "campaign", "agents", "chief", "coord")
    log31 = _read(os.path.join(coord, "ITER31_FITTARGET_CAPFIT", "driver_iter31.log"))
    log33 = _read(os.path.join(coord, "ITER33_C5NG_KAXIS", "driver_iter33.log"))
    log36 = _read(os.path.join(coord, "ITER36_DIESCRACK_Z", "driver_iter36.log"))
    log39 = _read(os.path.join(coord, "ITER39_DUALMOM_WIN", "driver_iter39.log"))
    log30 = _read(os.path.join(coord, "ITER30_RECIPE_SWEEP", "driver_iter30.log"))
    assert "3.787991" in log31, "ITER31 A3-at-cap reveal must be on record"
    assert "3.758975" in log33, "ITER33 k=3.5 reveal must be on record"
    assert "3.758736" in log36, "ITER36 Z=1.75 reveal must be on record"
    assert "3.754857" in log39, "ITER39 WIN=150 reveal must be on record"
    assert "3.754071" in log30, "ITER30 recipe-argmax reveal must be on record"
    ranking = [3.787991, 3.767511, 3.758975, 3.758736, 3.754857, 3.754071]
    assert ranking == sorted(ranking, reverse=True), "ITER40 must rank second-strongest rejected candidate"
    assert abs(3.767511 - 3.751429 - 0.016082) < 5e-7, "the recorded delta must be +0.016082"
