"""ITER51 C5ng-family vt_ann STALENESS RE-ADJUDICATION pins (session 31). 2026-09-20.

Pins the honest-negative verdict of the 27th measured axis: the C5ng family
harness vol-target grid (ITER48 mirror, VERBATIM: anchor 0.10 + 0.06/0.09/0.12/0.15)
re-adjudicated at the CURRENT champion (cfa9ec4d38158691) after the ITER49
adoption rescale (QAxasts 7.9566 -> 5.5133 pct; family share 31.61 -> 32.86 pct).
NO-ADMISSION, single clean run: the interior peak is EXACTLY at the committed
anchor VT=0.10 (IS-SR 4.218504 = the bar); every other arm sits below the bar,
the down-arm 0.09 through the Wmax wall (projid > 0, the ITER48 wall-shadow
channel at the new covariance); the up-arms 0.12/0.15 admissible but IS-dominated.
No reveal consumed per the sealed stop rule; no candidate CSV may exist. The
ITER48 interior-peak certificate SURVIVES the rescale - FIFTH independent plateau
confirmation (ITER22 weights / ITER29 estimator / ITER30 recipe / ITER50 solver /
ITER51 C5ng-vt-at-current-champion).
Mutation-checked: fake arm IS-SR / fake admission / fake verdict -> RED.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER51_C5NG_VT_READJ"
LOG = D + "/driver_iter51.log"
LOG_SHA = "717fb13980a137e3"
PRECOMMIT_SHA = "020a8e69de643117"
BAR = 4.218504


def _log():
    return open(LOG).read()


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def test_log_is_immutable_and_sealed():
    assert _sha(LOG) == LOG_SHA
    lg = _log()
    assert PRECOMMIT_SHA in lg.splitlines()[0]
    assert "FROZEN-BLOCK check" in lg and "driver_iter41" in lg and "driver_iter36" in lg


def test_anchor_arm_is_committed_continuity():
    lg = _log()
    assert "ARM VT=0.10: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg


def test_grid_is_sealed_mirror_and_interior_peaked_at_anchor():
    lg = _log()
    arms = re.findall(r"ARM VT=([0-9.]+): rows=1809 k=11 projid=([0-9.e+-]+) IS-SR=([0-9.]+) IS-MDD=(-[0-9.]+) pct negyrs=0 Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 5, len(arms)
    cells = dict((float(v), (float(pid), float(sr), float(mdd_), float(w))) for v, pid, sr, mdd_, w in arms)
    assert set(cells) == set((0.10, 0.06, 0.09, 0.12, 0.15)), sorted(cells)
    # interior peak EXACTLY at the committed anchor at the CURRENT frame (staleness refuted)
    assert cells[0.10][1] == 4.218504
    assert max(sr for pid, sr, mdd_, w in cells.values()) == cells[0.10][1]
    # wall-shadow channel: the IS-attractive down-arm 0.09 goes THROUGH the projection
    assert cells[0.09][0] > 0.0 and cells[0.09][3] >= 2.0
    assert cells[0.06][0] > 0.0 and cells[0.06][3] >= 2.0
    # projection IDENTITY on the incumbent (anchor + A2)
    assert cells[0.10][0] == 0.0
    # up-arms admissible but IS-dominated below the bar
    assert cells[0.12][0] == 0.0 and cells[0.12][1] < BAR
    assert cells[0.15][0] == 0.0 and cells[0.15][1] < BAR


def test_no_admission_structural_law():
    lg = _log()
    assert "IS admission: [] (bar 4.218504, anchor arm ineligible by construction)" in lg
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in lg
    assert "REVEAL" not in lg
    cand = [f for f in os.listdir(D) if f.startswith("candidate_")]
    assert cand == [], "candidate CSV must not exist under no-admission"
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_vt") and f.endswith("_weights.csv")]
    assert len(arms) == 5, arms


def test_champion_stable_and_precommit_intact():
    lg = _log()
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter51.py").read()
    # the family convention: projection IS used (ITER22 filter), identity on the incumbent
    assert "relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)" in drv
    # D19 guard: the reveal label FORMATS FS_BAR, no inherited literal
    assert "(incumbent %.6f)" in drv and "(incumbent 3." not in drv
    assert 'FS_BAR, f_ann_a' in drv


def test_vt_curve_both_directions_at_current_frame():
    lg = _log()
    # down direction (de-scale -> wall binds at the new covariance)
    assert "ARM VT=0.06: rows=1809 k=11 projid=3.579e-02 IS-SR=4.053512 IS-MDD=-2.5583 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM VT=0.09: rows=1809 k=11 projid=7.658e-03 IS-SR=4.207912 IS-MDD=-2.5627 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    # up direction (admissible, monotone falling)
    assert "ARM VT=0.12: rows=1809 k=11 projid=0.000e+00 IS-SR=4.184495 IS-MDD=-2.5843 pct negyrs=0 Wmax_sf=1.7843x grossmax=1.000000000" in lg
    assert "ARM VT=0.15: rows=1809 k=11 projid=0.000e+00 IS-SR=4.021775 IS-MDD=-2.6136 pct negyrs=0 Wmax_sf=1.5595x grossmax=1.000000000" in lg
    # fit-landing jitter margin: 1e-4 admission margin exceeds the measured jitter
    assert "A2b regen-vs-committed fit-landing jitter: weights 5.484e-09  IS-SR 7.868e-10" in lg
