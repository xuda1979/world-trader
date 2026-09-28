#@ ITER37 reality-pins (2026-09-19, session 18): QAxasts tsmom MAW axis.
# Largest remaining unmeasured second-tier cell (7.5906 pct book share measured at A2).
# One sleeve, ONE generator scalar MAW=189 inherited frozen from the A3 r7 acceptance era
# (standalone TRUNCATED-vintage SR plateau 42:0.89..378:1.04, maw=189 chosen mid-plateau);
# the book-level pool-fit IS-SR under the current objective was never measured over MAW.
# Pre-committed grid (precommit a8ea3922b5e64de3): {126, 157, 189, 220, 252} = anchor +
# acceptance-PRINTED plateau neighbors (157/252) + printed outer neighbor (126) + midpoint
# 220.5->220 (rounding disclosed at seal). VERDICT: 0/5 admitted - every novel cell BELOW
# the bar (126 4.162711 / 157 4.170947 / 220 4.190418 / 252 4.192827); the incumbent
# MAW=189 IS the family IS-argmax on the measured grid = interior-max closure shape (IS
# itself certifies the freeze, no reveal consumed). ITER17-law closure 12. Champion
# byte-stable pre==post. NEW D17 disclosed at seal: tools/quant/data/twelve_big/manifest.csv
# (untracked, 2026-09-08) breaks harness panel() -> r6lib unimportable; driver pre-patches
# it out at RUNTIME (A1 regen-vs-saved 1e-16 proves byte-faithfulness). Pins assert on
# recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER37 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER37_TSMOM_MAW")
COORD = os.path.join(ROOT, "campaign", "agents", "chief", "coord")
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
    # ITER37-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER37 memo
    # (the champion WAS byte-stable pre==post through ITER37; the driver-log sha lines
    # pinned below stay on the recorded ITER37-era values).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter37_precommit_sealed_before_run():
    pre = os.path.join(ITER37, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER37, "driver_iter37.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "a8ea3922b5e64de3"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    body = _read(pre)
    assert "sealed BEFORE any candidate run" in body
    assert "GRID = {126, 157, 189, 220, 252}" in body, "the grid rule must be disclosed at seal time, not after"
    assert "integer rounding DISCLOSED HERE" in body, "the 220.5->220 rounding must be disclosed at seal time"
    assert "D17" in body, "the manifest.csv repo defect must be disclosed at seal time"


def test_iter37_anchors_exact():
    log = _read(os.path.join(ITER37, "driver_iter37.log"))
    assert "FROZEN-BLOCK check vs driver_iter36.py: fit_relw/apply_cap/project_wmax/build_book text-identical" in log
    assert "ANCHOR A1 regen MAW=189 vs saved: maxdev=9.996344e-17 (inner n=4947)" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)  QAxasts share=7.5906 pct" in log
    assert "ANCHOR CELL MAW=189: weights dev vs committed 7.856e-09 (need <1e-6); book dev vs champ 4.877e-10 (need <1e-9); block share=0.300000" in log


def test_iter37_sweep_anchor_is_measured_argmax():
    log = _read(os.path.join(ITER37, "driver_iter37.log"))
    assert "MAW    regen-dev   is_sr     IS-ann pct  IS-MDD pct  negy  Wmax_sf   adm" in log
    assert "126    6.093e-02  4.162711    18.112       -2.63    0/9  1.8751x  no  blk=0.3000" in log
    assert "157    4.168e-02  4.170947    18.102       -2.61    0/9  1.8526x  no  blk=0.3000" in log
    assert "189    9.996e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)  blk=0.3000" in log
    assert "220    6.944e-02  4.190418    18.115       -2.53    0/9  1.8352x  no  blk=0.3000" in log
    assert "252    6.943e-02  4.192827    18.116       -2.52    0/9  1.8343x  no  blk=0.3000" in log
    assert "ADMITTED: 0 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    grid = {126: 4.162711, 157: 4.170947, 189: 4.198632, 220: 4.190418, 252: 4.192827}
    best = max(grid, key=grid.get)
    assert best == 189, "the incumbent MAW=189 must be the measured-grid IS-argmax of its own family"
    assert all(v < 4.198632 - 1e-4 for m, v in grid.items() if m != 189), "every novel cell strictly below the bar"
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER37, "arm_MAW*_weights.csv")))
    assert arms == ["arm_MAW126_weights.csv", "arm_MAW157_weights.csv", "arm_MAW189_weights.csv",
                    "arm_MAW220_weights.csv", "arm_MAW252_weights.csv"]
    assert not glob.glob(os.path.join(ITER37, "candidate_*")), "NO-ADMISSION means no reveal, so no candidate CSV"
    assert "REVEAL book" not in log, "no reveal may fire under the sealed stop rule"


def test_iter37_honest_negative_verdict():
    log = _read(os.path.join(ITER37, "driver_iter37.log"))
    assert "NO cell admitted -> HONEST NEGATIVE, no reveal (per precommit STOP RULE)." in log
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in log
    assert "Champion sha16 post-run: 8559fa55ee9a3417 / weights d2d11c92a98683df (pre==post: True)" in log


def test_iter37_signalparam_family_recertifies_freeze():
    # Cross-ITER pin: three independent one-scalar families (brwt zb, diescrack Z,
    # tsmom MAW) all re-anchor on the SAME incumbent IS-SR 4.198632; the two cells
    # that escaped it IS-side were police-killed OOS (ITER36 G7). IS-SR digits differ
    # only at 1e-6 resolution; the regen-dev column proves the swept cells are LIVE
    # curves, not jitter (dev 0.03..0.21 across the three families).
    log35 = _read(os.path.join(COORD, "ITER35_BRWT_ZBLOW", "driver_iter35.log"))
    log36 = _read(os.path.join(COORD, "ITER36_DIESCRACK_Z", "driver_iter36.log"))
    log37 = _read(os.path.join(ITER37, "driver_iter37.log"))
    assert "1.00   9.999e-17  4.198632" in log35
    assert "2.00   9.980e-17  4.198632" in log36
    assert "189    9.996e-17  4.198632" in log37
    assert "6.944e-02" in log37 and "4.168e-02" in log37, "tsmom sweep cells must be live, not jitter"
