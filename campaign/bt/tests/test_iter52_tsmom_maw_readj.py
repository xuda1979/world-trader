"""ITER52 QAxasts tsmom MAW STALENESS RE-ADJUDICATION pins (session 32). 2026-09-20.

Pins the honest-negative verdict of the 28th measured axis: the tsmom signal
moving-average window (ITER37 grid, VERBATIM: anchor 189 + 126/157/220/252,
vt FROZEN at the current 0.15 anchor) re-adjudicated at the CURRENT champion
(cfa9ec4d38158691). The ITER37 interior-peak certificate (bar 4.198632 at the
8559fa55 frame, vt10 vintage) predates THREE adopted non-uniform rescales
(ITER43 A5r2-vt015, ITER47 A5r2-vt024, ITER49 tsmom-vt015 - the last replaced
the canonical sleeve file itself). NO-ADMISSION, single clean run: the interior
peak is EXACTLY at the committed anchor MAW=189 (IS-SR 4.218504 = the bar);
both down-arms 126/157 go THROUGH the Wmax wall (projid > 0, 2.0000x - the
wall-shadow channel, now wall-adjacent at the rescaled fit, firing on the
DOWN direction unlike ITER48/51); both up-arms 220/252 admissible but
IS-dominated (closest miss 252 at bar-0.0091). No reveal consumed per the
sealed stop rule; no candidate CSV may exist. SIXTH independent plateau
confirmation (ITER22 weights / ITER29 estimator / ITER30 recipe / ITER50
solver / ITER51 C5ng-vt / ITER52 tsmom-MAW-at-current-champion).
Mutation-checked: fake bar-beating arm / fake admission / fake verdict -> RED.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER52_TSMOM_MAW_READJ"
LOG = D + "/driver_iter52.log"
LOG_SHA = "badb4a960d53d785"
PRECOMMIT_SHA = "0e4c271945a4be28"
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
    assert "ARM MAW=189: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg


def test_grid_is_sealed_iter37_mirror_and_interior_peaked_at_anchor():
    lg = _log()
    arms = re.findall(r"ARM MAW=([0-9]+): rows=1809 k=11 projid=([0-9.e+-]+) IS-SR=([0-9.]+) IS-MDD=(-[0-9.]+) pct negyrs=0 Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 5, len(arms)
    cells = dict((int(v), (float(pid), float(sr), float(mdd_), float(w))) for v, pid, sr, mdd_, w in arms)
    assert set(cells) == set((189, 126, 157, 220, 252)), sorted(cells)
    # interior peak EXACTLY at the committed anchor at the CURRENT frame (staleness refuted)
    assert cells[189][1] == 4.218504
    assert max(sr for pid, sr, mdd_, w in cells.values()) == cells[189][1]
    # wall-shadow channel: BOTH down-arms go THROUGH the projection at the rescaled fit
    assert cells[126][0] > 0.0 and cells[126][3] >= 2.0
    assert cells[157][0] > 0.0 and cells[157][3] >= 2.0
    # projection IDENTITY on the incumbent (anchor + A2)
    assert cells[189][0] == 0.0
    # up-arms admissible but IS-dominated below the bar (the ITER37 252 tick-up persists, still short)
    assert cells[220][0] == 0.0 and cells[220][1] < BAR
    assert cells[252][0] == 0.0 and cells[252][1] < BAR


def test_no_admission_structural_law():
    lg = _log()
    assert "IS admission: [] (bar 4.218504, anchor arm ineligible by construction)" in lg
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in lg
    assert "REVEAL" not in lg
    cand = [f for f in os.listdir(D) if f.startswith("candidate_")]
    assert cand == [], "candidate CSV must not exist under no-admission"
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_maw") and f.endswith("_weights.csv")]
    assert len(arms) == 5, arms


def test_champion_stable_and_precommit_intact():
    lg = _log()
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter52.py").read()
    # the family convention: projection IS used (ITER22 filter), identity on the incumbent
    assert "relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)" in drv
    # vt FROZEN at the current anchor in every arm (the refused tsmom-vt cell untouched)
    assert "VT_FROZEN = 0.15" in drv and "vol_target(net.dropna(), vt_ann=VT_FROZEN)" in drv
    # D19 guard: the reveal label FORMATS FS_BAR, no inherited literal
    assert "(incumbent %.6f)" in drv and "(incumbent 3." not in drv
    assert 'FS_BAR, f_ann_a' in drv
    # the load-bearing dual-identity D17 patch is present (r6lib resolves the full-path form)
    assert "DHF.panel = _panel_d17_full" in drv


def test_maw_curve_both_directions_at_current_frame():
    lg = _log()
    # down direction (de-windowing -> wall binds at the rescaled, wall-adjacent fit)
    assert "ARM MAW=126: rows=1809 k=11 projid=2.032e-03 IS-SR=4.172832 IS-MDD=-2.6452 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM MAW=157: rows=1809 k=11 projid=4.503e-04 IS-SR=4.183629 IS-MDD=-2.6207 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    # up direction (admissible, falling short of the anchor)
    assert "ARM MAW=220: rows=1809 k=11 projid=0.000e+00 IS-SR=4.207128 IS-MDD=-2.5346 pct negyrs=0 Wmax_sf=1.9930x grossmax=1.000000000" in lg
    assert "ARM MAW=252: rows=1809 k=11 projid=0.000e+00 IS-SR=4.209368 IS-MDD=-2.5255 pct negyrs=0 Wmax_sf=1.9927x grossmax=1.000000000" in lg
    # fit-landing jitter margin: 1e-4 admission margin exceeds the measured jitter
    assert "A2b regen-vs-committed fit-landing jitter: weights 3.249e-09  IS-SR 1.151e-10" in lg
