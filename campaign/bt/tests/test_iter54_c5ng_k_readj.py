"""ITER54 C5ng-k STALENESS RE-ADJUDICATION pins (session 34). 2026-09-20.

Pins the FIRST certificate RE-AFFIRMATION of the staleness class: the C5ng calm-filter
scalar k=2.5 (ONE generator scalar shared by C5ng + C5ngsum, family share 32.8568 pct =
ranks 1+2 of 12), certificate ITER33 ("incumbent = local IS dip, argmax k=3.5, OOS-refused"
at the 8559fa55 frame), re-adjudicated at the CURRENT champion (cfa9ec4d38158691). Grid =
ITER33 VERBATIM (2.5 anchor + 1.5/2.0/3.0/3.5), vt FROZEN 0.10 (the re-sealed ITER51 cell).
Result: the certificate STANDS IN FULL at the current frame - argmax IDENTITY frame-invariant
(k=3.5 IS-SR 4.241001 > bar 4.218504, +0.022497), incumbent-dip shape persists (2.00 4.218574
above bar but under the 1e-4 admission tolerance; 3.00 4.218193 a hair below), projid 0
EVERYWHERE (no wall-shadow arm, contrast ITER52/53; the argmax arm sits wall-adjacent at
1.9956x). The ONE sealed reveal (k=3.50) PASSES the FS-SR prong (+0.001962 = 3.822319) but
DIES at the G7 bins on the SAME 2021-22 energy-crisis dyad that killed the identical arm at
the ITER33 frame (dSR -0.2741 vs -0.2537 then; 2/5 positive). VERDICT: REJECT, no second
reveal, no adoption; champion UNCHANGED (gross 1.0 <= 1.6 operator cap, cagr 23.92 pct
>= 20 pct floor). Mutation-checked: fake admitted arm + fake admission list, and fake
ADOPTABLE verdict + fake G7 PASS + fake FS SR -> RED, then byte-exact restore -> GREEN.
"""
import hashlib
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER54_C5NG_K_READJ"
LOG = D + "/driver_iter54.log"
LOG_SHA = "b49b33f2320abfbb"
PRECOMMIT_SHA = "96f3078f6c940b06"
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
    assert "ARM K=2.50: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504 (bar 4.218504)" in lg
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg


def test_grid_is_sealed_iter33_mirror_and_argmax_identity_stands():
    lg = _log()
    arms = re.findall(r"ARM K=([0-9.]+): rows=1809 k=11 projid=([0-9.e+-]+) IS-SR=([0-9.]+) IS-MDD=(-[0-9.]+) pct negyrs=0 Wmax_sf=([0-9.]+)x", lg)
    assert len(arms) == 5, len(arms)
    cells = dict((round(float(v), 2), (float(pid), float(sr), float(w))) for v, pid, sr, mdd_, w in arms)
    assert set(cells) == set((2.5, 1.5, 2.0, 3.0, 3.5)), sorted(cells)
    # anchor = committed continuity at the bar
    assert cells[2.5][1] == 4.218504 and cells[2.5][0] == 0.0
    # the ITER33 certificate argmax IDENTITY is frame-invariant: 3.5 is the grid argmax, above bar
    assert max(sr for pid, sr, w in cells.values()) == cells[3.5][1] > cells[2.5][1]
    # the incumbent-dip SHAPE persists: 3.00 < anchor < 2.00, 1.50 strictly lowest
    assert cells[3.0][1] < cells[2.5][1] < cells[2.0][1]
    assert min(sr for pid, sr, w in cells.values()) == cells[1.5][1]
    # NO wall-shadow anywhere (contrast ITER52/53): projection identity on ALL arms,
    # and every arm (incl. the argmax, at 1.9956x wall-adjacent) stays UNDER the 2.0x wall
    for pid, sr, w in cells.values():
        assert pid == 0.0 and w < 2.0


def test_admission_tolerance_and_single_reveal():
    lg = _log()
    assert "IS admission: [3.5] (bar 4.218504, anchor arm ineligible by construction)" in lg
    # the 2.00 arm is ABOVE the bar but UNDER the sealed 1e-4 admission tolerance:
    # 4.218574 - 4.218504 = +7.0e-05 < 1e-4 -> correctly NOT admitted
    assert "IS admission: [2.0" not in lg
    assert "REVEAL arm K=3.50" in lg
    assert "REVEAL arm K=2.00" not in lg and "REVEAL arm K=3.00" not in lg, "second reveal forbidden"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in lg
    assert "GATE 7 OOS police" in lg and "FAIL" in lg.split("GATE 7 OOS police")[1][:60]
    cand = [f for f in sorted(os.listdir(D)) if f.startswith("candidate_")]
    assert cand == ["candidate_k3.50_daily.csv"], cand
    arms = [f for f in sorted(os.listdir(D)) if f.startswith("arm_k") and f.endswith(".csv")]
    assert len(arms) == 15, arms


def test_champion_stable_and_precommit_intact():
    lg = _log()
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    drv = open(D + "/driver_iter54.py").read()
    # the family convention: projection IS used (ITER22 filter), identity on the incumbent
    assert "relw = project_wmax(relw_raw, k=kcov, block=B.BRWT_BLOCK)" in drv
    # vt FROZEN at 0.10 (the RE-SEALED ITER51 cell, untouched); k is the swept scalar
    assert "VT_FROZEN = 0.10" in drv and "vol_target(net, vt_ann=VT_FROZEN)" in drv
    assert "std().shift(1) * k" in drv and "shift(1) * 2.5" not in drv.replace("ARMS = (2.5,", "")
    # per-arm calendar + coverage asserts (ported from the iter49/52/53 class)
    assert "calendar moved with K" in drv and "frame coverage changed" in drv
    # D19 guard: the reveal label FORMATS FS_BAR, no inherited literal
    assert "(incumbent %.6f)" in drv and "(incumbent 3." not in drv
    # D17: iter51-form single-identity inert safety patch retained (r6lib-FREE chain)
    assert "DH.panel = _panel_d17" in drv
    assert "D17 pre-patch applied" in lg


def test_k_curve_both_directions_and_reveal_values_at_current_frame():
    lg = _log()
    assert "ARM K=1.50: rows=1809 k=11 projid=0.000e+00 IS-SR=4.193574 IS-MDD=-2.5554 pct negyrs=0 Wmax_sf=1.8229x grossmax=1.000000000" in lg
    assert "ARM K=2.00: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218574 IS-MDD=-2.5770 pct negyrs=0 Wmax_sf=1.9204x grossmax=1.000000000" in lg
    assert "ARM K=3.00: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218193 IS-MDD=-2.5658 pct negyrs=0 Wmax_sf=1.9430x grossmax=1.000000000" in lg
    assert "ARM K=3.50: rows=1809 k=11 projid=0.000e+00 IS-SR=4.241001 IS-MDD=-2.5680 pct negyrs=0 Wmax_sf=1.9956x grossmax=1.000000000" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 5.484e-09  IS-SR 7.868e-10" in lg
    # the reveal PASSES the FS-SR prong (positive delta) and dies on the bins alone
    assert "FS SR=3.822319 (incumbent 3.820357)" in lg
    assert "bin 2021-22 dSR=-0.2741" in lg

