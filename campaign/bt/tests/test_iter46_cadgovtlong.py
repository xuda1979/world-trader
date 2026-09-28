"""ITER46 census-remainder cell pins (session 26). 2026-09-19.

Pins the honest-negative verdict of the LAST legal census-screen cell (cad_govt_long,
pool-composition class, 22nd measured axis): IS-admitted at +0.021443, revealed once,
G7-killed 2/5. Mutation-checked: fake FS-SR / fake bin / fake verdict -> RED.
"""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER46_CADGOVTLONG"
LOG = D + "/driver_iter46.log"
LOG_SHA = "92fd6a2cb7b30065"
PRECOMMIT_SHA = "7027fd6f05e3c1cb"


def _log():
    return open(LOG).read()


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def test_log_is_immutable_and_sealed():
    assert _sha(LOG) == LOG_SHA
    lg = _log()
    assert PRECOMMIT_SHA in lg.splitlines()[0]
    assert "FROZEN-BLOCK check" in lg and "driver_iter45" in lg and "driver_iter36" in lg and "driver_iter43" in lg


def test_a1_sibling_anchors_exact():
    lg = _log()
    assert "A1 sibling cad_govt_10y (dur=9.5) regen-vs-ITER24-saved: ok=True maxdev=9.995e-17 inner=4918 committed_nonnan=4918" in lg
    assert "A1 sibling cad_govt_2y (dur=1.9) regen-vs-ITER24-saved: ok=True maxdev=9.975e-17 inner=4918 committed_nonnan=4918" in lg


def test_cell_and_a2_continuity():
    lg = _log()
    assert "CELL cadlong: rows=1780 k=12 projid=0.000e+00 share=0.045852 IS-SR=4.225176 IS-MDD=-2.3873 pct negyrs=0 Wmax_sf=1.8949x grossmax=1.000000000" in lg
    assert "weights maxdev=8.327e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.203733 (bar 4.203733)" in lg
    assert "IS admission: True" in lg and "margin +0.021443" in lg


def test_reveal_g7_reject_verdict():
    lg = _log()
    assert "FS SR=3.754843 (incumbent 3.764764)" in lg
    assert "bin 2017-18 dSR=-0.0058" in lg and "bin 2019-20 dSR=-0.0360" in lg
    assert "bin 2021-22 dSR=+0.0028" in lg and "bin 2023-24 dSR=+0.0512" in lg
    assert "bin 2025-26 dSR=-0.0180" in lg
    assert "GATE 7 OOS police                   FAIL" in lg
    assert "GATE 1 FS ann>=20pct                PASS" in lg
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in lg


def test_champion_byte_stable_pre_post():
    lg = _log()
    assert "Champion sha16 pre-run: e67446186e269b88 / weights bde8612d0b295068" in lg
    assert "Champion sha16 post-run: e67446186e269b88 / weights bde8612d0b295068 (pre==post: True)" in lg


def test_amendment1_law_and_artifacts():
    pc = open(D + "/FINDINGS_PRECOMMIT.md").read()
    assert "Amendment 1" in pc and "RUN-1 FAIL-CLOSED" in pc and "5597f574c70f88c1" in pc
    drv = open(D + "/driver_iter46.py").read()
    assert "kcov == K_COVERED and (1809 - nrows) / 1809.0 <= 0.02" in drv
    assert "nrows == 1809 and kcov == K_COVERED" not in drv
    for f in ("anchor_iter46_a1.log", "arm_cadlong_stream.csv", "arm_cadlong_weights.csv",
              "candidate_cadlong_daily.csv", "FINDINGS.md"):
        assert os.path.isfile(D + "/" + f), f
