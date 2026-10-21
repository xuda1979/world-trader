"""ITER55 brwt-zb STALENESS RE-ADJUDICATION pins (session 35). 2026-09-20.

Pins the SECOND certificate RE-AFFIRMATION of the staleness class and the FIRST PURE one
(no police consumed at either frame): the brwt trio scalar zb=1.0 (ONE shared generator
scalar, trio 30.0000 pct = exactly the 0.30 block cap), certificate ITER34+35 (stitched
FULL INTERIOR-MAX at zb=1.0), re-adjudicated at the current champion (cfa9ec4d38158691)
across the stitched grid VERBATIM {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0}. Result:
strictly single-peaked at the incumbent at BOTH frames (the rescale lifted every cell
~+0.006..+0.013 and moved no ranking); zb=0.75 is the FIRST wall-captive cell of the
family (projid 1.878e-04 -> projected 2.0000x, denied by the pre-registered projid==0
addendum AND by IS-SR); admission EMPTY, no reveal, no candidate CSV; champion sha
pre==post. Mutation-checked: fake admitted arm, and fake reveal+ADOPTABLE verdict ->
RED, then byte-exact restore -> GREEN.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER55_BRWT_ZB_READJ"
LOG = D + "/driver_iter55.log"
LOG_SHA = "efe59d15ffbf4048"
PRECOMMIT_SHA = "3d9e4163bff420b1"
DRIVER_SHA = "c607d7fa9d90e9a5"


def _log():
    return open(LOG).read()


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def test_log_is_immutable_and_sealed():
    assert _sha(LOG) == LOG_SHA
    lg = _log()
    assert PRECOMMIT_SHA in lg.splitlines()[0]
    assert "ITER55 BRWT-ZB STALENESS RE-ADJUDICATION" in lg.splitlines()[0]
    assert "FROZEN-BLOCK check" in lg and "driver_iter41" in lg and "driver_iter36" in lg


def test_anchor_arm_is_committed_continuity():
    lg = _log()
    assert "ARM ZB=1.00: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg
    assert "A1 regen-zb100-vs-committed brwt10 ok=True maxdev=9.999e-17 inner=6567 committed_nonnan=6567" in lg
    assert "A1 regen-zb100-vs-committed brwt7 ok=True maxdev=9.986e-17 inner=4580 committed_nonnan=4580" in lg
    assert "A1 regen-zb100-vs-committed brwt5 ok=True maxdev=9.996e-17 inner=4580 committed_nonnan=4580" in lg


def test_grid_is_sealed_iter34plus35_mirror_and_interior_max_recertified():
    lg = _log()
    arms = re.findall(r"ARM ZB=([0-9.]+): rows=1809 k=11 projid=([0-9.e+-]+) IS-SR=([0-9.]+) IS-MDD=(-[0-9.]+) pct negyrs=0 Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 8, len(arms)
    cells = dict((round(float(v), 2), (float(pid), float(sr), float(w))) for v, pid, sr, m_, w in arms)
    assert set(cells) == set((1.0, 0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.0)), sorted(cells)
    # anchor = committed continuity at the bar, projection identity
    assert cells[1.0][1] == 4.218504 and cells[1.0][0] == 0.0
    # certificate RE-AFFIRMED: strictly single-peaked at the incumbent at this frame too
    assert cells[0.25][1] < cells[0.5][1] < cells[0.75][1] < cells[1.0][1]
    assert cells[1.0][1] > cells[1.25][1] > cells[1.5][1] > cells[1.75][1] > cells[2.0][1]
    assert max(sr for _, sr, _ in cells.values()) == cells[1.0][1]
    assert min(sr for _, sr, _ in cells.values()) == cells[2.0][1]
    # the pre-registered addendum FIRED: 0.75 is the family's first wall-captive cell
    assert cells[0.75][0] > 0.0, "0.75 must remain the projected wall-captive arm"
    # every other arm is projection-identity and under the wall
    for z, (pid, sr, w) in sorted(cells.items()):
        if z != 0.75:
            assert pid == 0.0 and w < 2.0, (z, pid, w)


def test_no_admission_no_reveal_no_candidate():
    lg = _log()
    assert "IS admission: [] (bar 4.218504, anchor ineligible, projid==0 addendum per precommit)" in lg
    assert "NO non-anchor arm IS-admitted -> HONEST NEGATIVE, no reveal (sealed stop rule)." in lg
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in lg
    assert "REVEAL arm" not in lg, "no reveal may fire under no-admission"
    cand = [f for f in sorted(os.listdir(D)) if f.startswith("candidate_")]
    assert cand == [], cand
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_zb") and f.endswith(".csv")]
    assert len(arms) == 32, arms


def test_champion_stable_and_precommit_and_driver_hygiene():
    lg = _log()
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    assert _sha(D + "/driver_iter55.py") == DRIVER_SHA
    drv = open(D + "/driver_iter55.py").read()
    # the family convention: projection IS used, identity on feasible vectors
    assert "relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)" in drv
    # pre-registered admission addendum present in source (projid gate)
    assert 'and results[z]["proj_id"] == 0.0' in drv
    # brwt vt = harness DEFAULT form (not a swept scalar)
    assert "scaled, _ = vol_target(net)" in drv and "vt_ann" not in drv
    # per-arm calendar + coverage asserts (ported lineage)
    assert "calendar moved with ZB" in drv and "frame coverage changed" in drv
    # D19 guard extended: NO iter54 token survives in ANY case (the log-filename defect class)
    assert "iter54" not in drv.lower()
    assert "ANCHOR_ZB = 1.0" in drv and "ARMS = (1.0, 0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.0)" in drv
    # D17: iter51-form single-identity inert safety patch retained (r6lib-FREE chain)
    assert "DH.panel = _panel_d17" in drv
    assert "D17 pre-patch applied" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 1.050e-08  IS-SR 6.066e-10" in lg


def test_zb_curve_values_at_current_frame_vs_cert_frame():
    lg = _log()
    assert "ARM ZB=0.25: rows=1809 k=11 projid=0.000e+00 IS-SR=3.904022 IS-MDD=-4.3066 pct negyrs=0 Wmax_sf=1.9273x grossmax=1.000000000" in lg
    assert "ARM ZB=0.50: rows=1809 k=11 projid=0.000e+00 IS-SR=4.067581 IS-MDD=-3.6387 pct negyrs=0 Wmax_sf=1.9702x grossmax=1.000000000" in lg
    assert "ARM ZB=0.75: rows=1809 k=11 projid=1.878e-04 IS-SR=4.189759 IS-MDD=-2.9869 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM ZB=1.25: rows=1809 k=11 projid=0.000e+00 IS-SR=4.072818 IS-MDD=-3.2455 pct negyrs=0 Wmax_sf=1.9428x grossmax=1.000000000" in lg
    assert "ARM ZB=2.00: rows=1809 k=11 projid=0.000e+00 IS-SR=3.237666 IS-MDD=-2.2839 pct negyrs=0 Wmax_sf=1.8247x grossmax=1.000000000" in lg
