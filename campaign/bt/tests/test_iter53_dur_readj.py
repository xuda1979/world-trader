"""ITER53 a6r7 DUR STALENESS RE-ADJUDICATION pins (session 33). 2026-09-20.

Pins the FIRST certificate movement on record + the police kill: the a6r7
generator duration scalar (ITER32 grid, VERBATIM: anchor 1.90 + 1.40/1.65/2.15/
2.40, legacy 6.0bp / K=378 / CAD=42 / VT=0.12 CAP=5.0 FROZEN) re-adjudicated at
the CURRENT champion (cfa9ec4d38158691). The ITER32 interior-peak certificate
("anchor = grid argmax", bar 4.198632 at the 8559fa55 frame) predates THREE
adopted non-uniform rescales. Result: the interior peak MOVED off the anchor
DOWN-axis to 1.65 (IS-SR 4.220444 > bar 4.218504; 1.40 also admitted at
4.220132) - staleness CONFIRMED at IS level, the first movement under the
class (ITER50/51/52 all returned the incumbent). The up-arms 2.15/2.40 go
THROUGH the Wmax wall (mirror of ITER52's down-arms; the rescaled fit sits
wall-adjacent at 1.9736x). The ONE sealed reveal (IS-argmax 1.65) DIED at the
G7 OOS police: FS SR 3.810315 < 3.820357 and 3/5 positive bins - the IS gain
inverts OOS. VERDICT: REJECT, no second reveal, no adoption; champion
UNCHANGED (gross 1.0 <= 1.6 operator cap, cagr 23.92 pct >= 20 pct floor).
Mutation-checked: fake admission line / fake verdict -> RED.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER53_DUR_READJ"
LOG = D + "/driver_iter53.log"
LOG_SHA = "97cdc606e45af7a3"
PRECOMMIT_SHA = "710a1e7de776dbbd"
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
    assert "ARM DUR=1.90: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg


def test_grid_is_sealed_iter32_mirror_and_peak_moved_off_anchor():
    lg = _log()
    arms = re.findall(r"ARM DUR=([0-9.]+): rows=1809 k=11 projid=([0-9.e+-]+) IS-SR=([0-9.]+) IS-MDD=(-[0-9.]+) pct negyrs=0 Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 5, len(arms)
    cells = dict((round(float(v), 2), (float(pid), float(sr), float(w))) for v, pid, sr, mdd_, w in arms)
    assert set(cells) == set((1.9, 1.4, 1.65, 2.15, 2.4)), sorted(cells)
    # anchor = committed continuity at the bar; the interior peak has MOVED off it (staleness CONFIRMED)
    assert cells[1.9][1] == 4.218504 and cells[1.9][0] == 0.0
    assert max(sr for pid, sr, w in cells.values()) == cells[1.65][1] > cells[1.9][1]
    # admitted down-arms: projection IDENTITY (wall released) at the rescaled wall-adjacent fit
    assert cells[1.4][0] == 0.0 and cells[1.4][2] < 2.0
    assert cells[1.65][0] == 0.0 and cells[1.65][2] < 2.0
    # up-arms THROUGH the wall (mirror of ITER52's down-arms)
    assert cells[2.15][0] > 0.0 and cells[2.15][2] >= 2.0
    assert cells[2.4][0] > 0.0 and cells[2.4][2] >= 2.0


def test_reveal_argmax_and_g7_reject_structural():
    lg = _log()
    assert "IS admission: [1.4, 1.65] (bar 4.218504, anchor arm ineligible by construction)" in lg
    assert "REVEAL arm DUR=1.65" in lg
    assert "REVEAL arm DUR=1.40" not in lg, "second reveal forbidden by the sealed stop rule"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in lg
    assert "GATE 7 OOS police" in lg and "FAIL" in lg.split("GATE 7 OOS police")[1][:60]
    assert "FS SR=3.810315 (incumbent 3.820357)" in lg
    cand = [f for f in sorted(os.listdir(D)) if f.startswith("candidate_")]
    assert cand == ["candidate_dur1.65_daily.csv"], cand
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_dur") and f.endswith(".csv")]
    assert len(arms) == 10, arms


def test_champion_stable_and_precommit_intact():
    lg = _log()
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter53.py").read()
    # the family convention: projection IS used (ITER22 filter), identity on the incumbent
    assert "relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)" in drv
    # a6r7 convention FROZEN: legacy 6.0bp inside the sleeve, VT=0.12/CAP=5.0 inline (vt cell untouched)
    assert "K, CAD, VT, CAP = 378, 42, 0.12, 5.0" in drv and "turn * 6.0 / 1e4" in drv
    # D19 guard: the reveal label FORMATS FS_BAR, no inherited literal
    assert "(incumbent %.6f)" in drv and "(incumbent 3." not in drv
    # D17 scope: r6lib-FREE chain, iter52-form dual patch substituted OUT, scope note logged
    assert "D17 SCOPE NOTE" in drv
    assert "DHF.panel" not in drv and "_panel_d17" not in drv


def test_dur_curve_both_directions_at_current_frame():
    lg = _log()
    assert "ARM DUR=1.40: rows=1809 k=11 projid=0.000e+00 IS-SR=4.220132 IS-MDD=-2.5573 pct negyrs=0 Wmax_sf=1.7425x grossmax=1.000000000" in lg
    assert "ARM DUR=1.65: rows=1809 k=11 projid=0.000e+00 IS-SR=4.220444 IS-MDD=-2.5664 pct negyrs=0 Wmax_sf=1.8676x grossmax=1.000000000" in lg
    assert "ARM DUR=2.15: rows=1809 k=11 projid=2.243e-03 IS-SR=4.215853 IS-MDD=-2.5738 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM DUR=2.40: rows=1809 k=11 projid=6.372e-03 IS-SR=4.213369 IS-MDD=-2.5774 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 7.684e-09  IS-SR 1.210e-09" in lg
