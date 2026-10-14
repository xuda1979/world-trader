#@ ITER38 reality-pins (2026-09-19, session 19): dualmom hysteresis-BAND axis at frozen WIN=200.
# dualmom = QA_dualmom_band121 (A3 r2 accepted, 5.7226 pct book share measured at A2), the last
# second-tier cell with an admissible 1-D slice. 2-D (win x band) surface REFUSED at seal; the
# pre-committed 1-D rule: sweep the threshold (BAND) at frozen window WIN=200 (diescrack class;
# BAND is the sleeve's namesake scalar). Grid = EXACTLY the acceptance-printed band axis
# (at{0.01, 0.02, 0.03, 0.04, 0.05}, r2_scan5.py) - zero new points, anchor centered.
# VERDICT: 1/5 admitted (BAND=0.02 at IS-SR 4.199008 = bar + 0.000376, shadow-price scale);
# REVEAL fired: FS SR 3.750604 < 3.751429 AND G7 bins 1/5 positive => REJECT (ITER17-law
# closure 13). Curve single-peaked with the peak at 0.02: the incumbent freeze sits AT the
# interior max within jitter. Champion byte-stable pre==post. D17 panel() pre-patch carried;
# A1 regen-vs-saved 9.996344e-17 with INDEX IDENTICAL (re-type byte-faithful incl. calendar).
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER38 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER38_DUALMOM_BAND")
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
    # ITER38-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER38 memo
    # (the champion WAS byte-stable pre==post through ITER38; the driver-log sha lines
    # pinned in test_iter38_champion_byte_stable_and_disclosures stay on the recorded
    # ITER38-era values).
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(CHAMP) == "a8ed233bd0f6fd5d"
    assert _sha16(WGT) == "2b0f5fbc43113149"


def test_iter38_precommit_sealed_before_run():
    pre = os.path.join(ITER38, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER38, "driver_iter38.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "8a1c571db36f9770"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    body = _read(pre)
    assert "Sealed BEFORE any candidate computation" in body
    assert "GRID = " + LB + "0.01, 0.02, 0.03, 0.04, 0.05" + RB in body, "grid rule must be disclosed at seal time"
    assert "2-D surface REFUSED at seal" in body, "the 25-cell mining refusal must be at seal time"
    assert "D17" in body, "the manifest.csv repo defect must be disclosed at seal time"
    assert "9.996344e-17" in body, "pre-seal A1 result must be disclosed inside the precommit"


def test_iter38_anchors_exact():
    log = _read(os.path.join(ITER38, "driver_iter38.log"))
    assert "FROZEN-BLOCK check vs driver_iter36.py + driver_iter37.py: fit_relw/apply_cap/project_wmax/build_book text-identical" in log
    assert "ANCHOR A1 regen BAND=0.03 vs saved: maxdev=9.996344e-17 (inner n=4743)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)  dualmom share=5.7226 pct" in log
    assert "ANCHOR CELL BAND=0.03: weights dev vs committed 7.527e-09 (need <1e-6); book dev vs champ 4.468e-10 (need <1e-9); block share=0.300000" in log
    alog = _read(os.path.join(ITER38, "anchor_iter38.log"))
    assert "index identical: True" in alog, "re-type calendar must be byte-identical to the committed emission"


def test_iter38_band_curve_single_peak_at_002():
    log = _read(os.path.join(ITER38, "driver_iter38.log"))
    assert "0.01   8.210e-02  4.188768    18.100       -2.56    0/9  1.8152x  no  blk=0.3000" in log
    assert "0.02   2.181e-02  4.199008    18.121       -2.56    0/9  1.8114x  YES  blk=0.3000" in log
    assert "0.03   9.996e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "0.04   5.732e-02  4.193199    18.115       -2.56    0/9  1.8164x  no  blk=0.3000" in log
    assert "0.05   5.589e-02  4.185947    18.087       -2.56    0/9  1.8078x  no  blk=0.3000" in log
    assert "ADMITTED: 1 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = dict(zip(("0.01", "0.02", "0.03", "0.04", "0.05"),
                    (4.188768, 4.199008, 4.198632, 4.193199, 4.185947)))
    best = max(grid, key=grid.get)
    assert best == "0.02", "the measured band curve must peak at 0.02, not at the anchor"
    assert grid["0.02"] > grid["0.03"] > grid["0.04"] > grid["0.05"], "right side falls monotonically from the peak"
    assert grid["0.02"] > grid["0.01"], "left side rises into the peak - full printed envelope measured"
    assert 4.198632 < grid["0.02"] and grid["0.02"] - 4.198632 < 5e-4, "escape cell is shadow-price scale only"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER38, "arm_BAND*_weights.csv")))
    assert len(arms) == 5, "one weights CSV per swept cell"


def test_iter38_reveal_police_killed():
    log = _read(os.path.join(ITER38, "driver_iter38.log"))
    assert "GLOBAL ARGMAX (IS-only): BAND=0.02 IS-SR=4.199008 Wmax_sf=1.8114x block=0.300000" in log
    assert "REVEAL book: 12-pool refit at BAND=0.02, gear 1.0, n=4806 (2008-03-31..2026-08-28)" in log
    assert "FS SR=3.750604 (incumbent 3.751429)" in log
    assert 3.750604 < 3.751429, "the IS gain must INVERT at full sample (FS SR below the incumbent)"
    assert "bin 2017-18 dSR=-0.0006" in log
    assert "bin 2019-20 dSR=+0.0015" in log
    assert "bin 2021-22 dSR=-0.0059" in log
    assert "bin 2023-24 dSR=-0.0076" in log
    assert "bin 2025-26 dSR=-0.0005" in log
    assert "GATE 7 OOS police             FAIL" in log
    assert log.count("REVEAL book") == 1, "no second reveal per sealed stop rule"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in log
    assert _sha16(os.path.join(ITER38, "candidate_BAND0.02_daily.csv"))
    assert _sha16(os.path.join(ITER38, "candidate_BAND0.02_weights.csv"))


def test_iter38_champion_byte_stable_and_disclosures():
    log = _read(os.path.join(ITER38, "driver_iter38.log"))
    assert "Champion sha16 pre-run: 8559fa55ee9a3417 / weights d2d11c92a98683df / precommit 8a1c571db36f9770" in log
    assert "Champion sha16 post-run: 8559fa55ee9a3417 / weights d2d11c92a98683df (pre==post: True)" in log
    pre = _read(os.path.join(ITER38, "FINDINGS_PRECOMMIT.md"))
    assert "manifest.csv skipped" in pre or "pre-patches harness panel()" in pre
    assert "first eligible MES 2007-09-28" in pre, "coverage-law expectation must be pre-stated"

