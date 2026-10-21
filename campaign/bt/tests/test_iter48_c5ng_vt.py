"""ITER48 C5ng family vol-target axis pins (session 28). 2026-09-19.

Pins the honest-negative verdict of the LARGEST-weight family's harness vt axis
(24th measured axis; C5ng+C5ngsum = 31.61 pct of the vt024 book): NO-ADMISSION,
single clean run - IS curve SINGLE-PEAKED with the interior peak EXACTLY at the
committed vt=0.10 anchor; wall-shadow confirmed on the down-scale arms
(Wmax_sf pinned 2.0000x, water-filling active). No reveal consumed per the
sealed stop rule; no candidate CSV may exist. Mutation-checked: fake arm
IS-SR / fake verdict / fake champion sha -> RED.
"""
import hashlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER48_C5NG_VT"
LOG = D + "/driver_iter48.log"
LOG_SHA = "8f73335c33f615e0"
PRECOMMIT_SHA = "0ceea07f0c18cf32"


def _log():
    return open(LOG).read()


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def test_log_is_immutable_and_sealed():
    assert _sha(LOG) == LOG_SHA
    lg = _log()
    assert PRECOMMIT_SHA in lg.splitlines()[0]
    assert "FROZEN-BLOCK check" in lg and "driver_iter41" in lg and "driver_iter36" in lg


def test_a1_anchors_exact():
    lg = _log()
    assert "A1a regen-vt010-vs-committed C5ng ok=True maxdev=9.975e-17 inner=7381 committed_nonnan=7381" in lg
    assert "A1b regen-vt010-vs-committed C5ngsum ok=True maxdev=9.996e-17 inner=7381 committed_nonnan=7381" in lg


def test_arm_curve_interior_peak_at_anchor():
    lg = _log()
    assert "ARM VT=0.06: rows=1809 k=11 projid=3.308e-02 IS-SR=4.039271 IS-MDD=-2.5461 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM VT=0.09: rows=1809 k=11 projid=8.215e-04 IS-SR=4.195859 IS-MDD=-2.5574 pct negyrs=0 Wmax_sf=2.0000x grossmax=1.000000000" in lg
    assert "ARM VT=0.10: rows=1809 k=11 projid=0.000e+00 IS-SR=4.207736 IS-MDD=-2.5649 pct negyrs=0 Wmax_sf=1.8989x grossmax=1.000000000" in lg
    assert "ARM VT=0.12: rows=1809 k=11 projid=0.000e+00 IS-SR=4.182824 IS-MDD=-2.5782 pct negyrs=0 Wmax_sf=1.7112x grossmax=1.000000000" in lg
    assert "ARM VT=0.15: rows=1809 k=11 projid=0.000e+00 IS-SR=4.030003 IS-MDD=-2.5995 pct negyrs=0 Wmax_sf=1.4803x grossmax=1.000000000" in lg


def test_a2_continuity_and_jitter():
    lg = _log()
    assert "weights maxdev=8.327e-17 bytes maxdev=9.988e-17 n=4806 rows=1809 k=11 IS-SR=4.207736 (bar 4.207736)" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 8.289e-09  IS-SR 1.465e-09" in lg


def test_no_admission_law_and_no_candidate_artifact():
    lg = _log()
    assert "IS admission: [] (bar 4.207736, anchor arm ineligible by construction)" in lg
    assert "VERDICT: NO-ADMISSION (IS level) -> honest negative, no reveal (per precommit stop rule)" in lg
    assert "REVEAL" not in lg
    cand = [f for f in os.listdir(D) if f.startswith("candidate_")]
    assert cand == [], "candidate CSV must not exist under no-admission"
    for vt in ("01", "006", "009", "012", "015"):
        assert os.path.isfile(D + "/arm_vt%s_stream_cng.csv" % vt), vt
        assert os.path.isfile(D + "/arm_vt%s_stream_sum.csv" % vt), vt
        assert os.path.isfile(D + "/arm_vt%s_weights.csv" % vt), vt


def test_champion_stable_and_machinery_law():
    lg = _log()
    assert "Champion sha16 pre-run: 3c456aa53193eb89 / weights 8313bee1ad8a72fe" in lg
    assert "Champion sha16 post-run: 3c456aa53193eb89 / weights 8313bee1ad8a72fe (pre==post: True)" in lg
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter48.py").read()
    assert "vol_target(net, vt_ann=vt)" in drv
    assert "build_a5r2" not in drv and "A5CSV" not in drv
