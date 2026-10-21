"""ITER50 book-solver (shrink, brwt-cap) re-adjudication pins (session 30). 2026-09-20.

Pins the honest-negative verdict of the 26th measured axis: the solver grid
(ITER22 15-pt + ITER23 7-edge, verbatim) re-adjudicated at the CURRENT champion
after two admitted non-uniform rescales (ITER47/49). NO-ADMISSION, single clean
run: every bar-beating cell breaches the Wmax 2.0x invariant (ITER23 structure
replicated at the new covariance); every admissible cell sits below the bar;
the anchor (0.70, 0.30) IS the admissible argmax, exactly. No projection used
(sealed ITER22 filter convention; projection is identity on the incumbent).
No reveal consumed per the sealed stop rule; no candidate CSV may exist.
Mutation-checked: fake arm IS-SR / fake wall breach / fake verdict -> RED.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER50_SHRINK_READJ"
LOG = D + "/driver_iter50.log"
LOG_SHA = "1a92e365c279c80a"
PRECOMMIT_SHA = "e9eaf0183cb2072c"
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


def test_anchor_cell_is_committed_continuity():
    lg = _log()
    assert "ARM s=0.70 c=0.30: rows=1809 k=11 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg


def test_grid_completeness_22_cells():
    lg = _log()
    arms = re.findall(r"ARM s=([0-9.]+) c=([0-9.]+): rows=1809 k=11 IS-SR=([0-9.]+).*Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 22, len(arms)
    cells = dict(((float(s), float(c)), (float(sr), float(w))) for s, c, sr, w in arms)
    assert (0.70, 0.30) in cells
    # strongest bar-beating cells, ALL wall-inadmissible (ITER23 structure at the new covariance)
    assert cells[(0.40, 0.30)][0] == 4.242558 and cells[(0.40, 0.30)][1] > 2.0
    assert cells[(0.50, 0.30)][0] == 4.235334 and cells[(0.50, 0.30)][1] > 2.0
    assert cells[(0.70, 0.27)][0] == 4.227197 and cells[(0.70, 0.27)][1] > 2.0
    # best WALL-ADMISSIBLE non-anchor cells remain BELOW the bar
    assert cells[(0.70, 0.25)][1] > 2.0
    assert max(sr for (s, c), (sr, w) in cells.items() if w <= 2.0 and (s, c) != (0.70, 0.30)) < BAR


def test_no_admission_structural_law():
    lg = _log()
    assert "IS admission: [] (bar 4.218504 = committed anchor, anchor cell ineligible by construction)" in lg
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in lg
    assert "REVEAL" not in lg
    cand = [f for f in os.listdir(D) if f.startswith("candidate_")]
    assert cand == [], "candidate CSV must not exist under no-admission"
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_s") and f.endswith("_weights.csv")]
    assert len(arms) == 22, arms


def test_no_projection_convention_and_champion_stable():
    lg = _log()
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter50.py").read()
    assert "def project_wmax" in drv, "frozen block stays defined"
    calls = [l for l in drv.splitlines() if "project_wmax(" in l and not l.strip().startswith("def ")]
    assert calls == [], "sealed no-projection convention: never called"
    assert "apply_cap(fit, cap=cp)" in drv and "shrink=sh" in drv

def test_edge_curve_values_both_axes():
    lg = _log()
    # de-concentration direction: IS-SR falls monotonically as shrink rises at cap 0.30
    assert "ARM s=0.98 c=0.30: rows=1809 k=11 IS-SR=4.184024 IS-MDD=-2.6729 pct negyrs=0 Wmax_sf=1.8360x grossmax=1.000000000" in lg
    assert "ARM s=0.85 c=0.30: rows=1809 k=11 IS-SR=4.202808 IS-MDD=-2.6182 pct negyrs=0 Wmax_sf=1.9104x grossmax=1.000000000" in lg
    # concentration direction at shrink 0.70: wall-shadow - the IS-attractive edge cells all breach
    assert "ARM s=0.70 c=0.29: rows=1809 k=11 IS-SR=4.223676 IS-MDD=-2.5112 pct negyrs=0 Wmax_sf=2.0018x grossmax=1.000000000" in lg
    assert "ARM s=0.60 c=0.30: rows=1809 k=11 IS-SR=4.227365 IS-MDD=-2.5430 pct negyrs=0 Wmax_sf=2.0125x grossmax=1.000000000" in lg
    # cap 0.25 rows: near-miss admissible de-concentration still below bar
    assert "ARM s=0.85 c=0.25: rows=1809 k=11 IS-SR=4.207594 IS-MDD=-2.3232 pct negyrs=0 Wmax_sf=2.0468x grossmax=1.000000000" in lg
    assert "ARM s=0.98 c=0.25: rows=1809 k=11 IS-SR=4.194032 IS-MDD=-2.3837 pct negyrs=0 Wmax_sf=1.9671x grossmax=1.000000000" in lg
