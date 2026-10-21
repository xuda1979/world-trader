"""ITER49 tsmom (QAxasts) harness vol-target axis pins (session 29). 2026-09-19.

Pins the THIRD ADOPTION of the campaign - the tsmom family slice 2 under the 38/39
two-slice standard (25th measured axis): harness vol_target vt_ann, grid mirrored from
the sealed ITER43/48 grid. IS curve monotone RISING through the anchor to the sealed
0.15 edge (2/4 admitted; anchor NOT the family argmax - the #48 shrink-distortion
signature, direction family-dependent). REVEAL vt=0.15: FS SR 3.820357 = +0.0363,
G7 4/5 positive bins min -0.0092, 8/8 gates -> battery -> ADOPTED. Champion of record
cfa9ec4d38158691 / weights a384d6b92e258fd5 / canonical sleeve
E1_QAxasts_tsmom189__vt015.csv. ANTI-DOG-CHASE binding: LAST seal on the tsmom family;
the rising edge is recorded, NOT chased. Mutation-checked: fake arm IS-SR / fake
verdict / fake log sha -> RED.
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = ROOT + "/campaign/agents/chief/coord/ITER49_TSMOM_VT"
LOG = D + "/driver_iter49.log"
LOG_SHA = "0560a282e776a429"
PRECOMMIT_SHA = "f79bb6dbf3001d45"


def _log():
    return open(LOG).read()


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def test_log_is_immutable_and_sealed():
    assert _sha(LOG) == LOG_SHA
    lg = _log()
    assert PRECOMMIT_SHA in lg.splitlines()[0]
    assert "FROZEN-BLOCK check" in lg and "driver_iter41" in lg and "driver_iter36" in lg
    assert "Amendment 1" in lg


def test_a1_anchor_exact():
    lg = _log()
    assert "A1 regen-vt010-vs-committed QAxasts ok=True maxdev=9.996e-17 inner=4947 committed_nonnan=4947" in lg


def test_arm_curve_rises_through_anchor_to_sealed_edge():
    lg = _log()
    assert "ARM VT=0.06: rows=1809 k=11 projid=0.000e+00 IS-SR=4.191405 IS-MDD=-2.5554 pct negyrs=0 Wmax_sf=1.7651x grossmax=1.000000000" in lg
    assert "ARM VT=0.09: rows=1809 k=11 projid=0.000e+00 IS-SR=4.204800 IS-MDD=-2.5633 pct negyrs=0 Wmax_sf=1.8752x grossmax=1.000000000" in lg
    assert "ARM VT=0.10: rows=1809 k=11 projid=0.000e+00 IS-SR=4.207736 IS-MDD=-2.5649 pct negyrs=0 Wmax_sf=1.8989x grossmax=1.000000000" in lg
    assert "ARM VT=0.12: rows=1809 k=11 projid=0.000e+00 IS-SR=4.212618 IS-MDD=-2.5675 pct negyrs=0 Wmax_sf=1.9355x grossmax=1.000000000" in lg
    assert "ARM VT=0.15: rows=1809 k=11 projid=0.000e+00 IS-SR=4.218504 IS-MDD=-2.5701 pct negyrs=0 Wmax_sf=1.9736x grossmax=1.000000000" in lg


def test_a2_continuity_and_jitter():
    lg = _log()
    assert "weights maxdev=8.327e-17 bytes maxdev=9.988e-17 n=4806 rows=1809 k=11 IS-SR=4.207736 (bar 4.207736)" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 4.221e-09  IS-SR 2.064e-09" in lg


def test_admission_reveal_adoptable_8of8():
    lg = _log()
    assert "IS admission: [0.12, 0.15] (bar 4.207736, anchor arm ineligible by construction)" in lg
    assert "REVEAL arm VT=0.15 (IS-argmax of admitted), gear 1.0, n=4806 (2008-03-31..2026-08-28)" in lg
    assert "  FS SR=3.820357 (incumbent 3.784099)  ann arith=21.6147 pct  cagr=23.9215 pct  MDD=-3.7339 pct  negyrs=0" in lg
    assert "  bin 2021-22 dSR=+0.0618 (cand 2.3310 vs inc 2.2692)" in lg
    for gate in ("1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
                 "5 CFX4=0", "6 Wmax_sf<=2.0x (k=11)", "7 OOS police", "8 fit-window shrink<=2pct"):
        line = [l for l in lg.splitlines() if ("GATE " + gate) in l][0]
        assert line.endswith("PASS"), gate
    assert "VERDICT: ADOPTABLE (8/8) -> proceed to full battery per precommit" in lg
    assert os.path.isfile(D + "/candidate_vt015_daily.csv")
    for vt in ("006", "009", "012", "015"):
        assert os.path.isfile(D + "/arm_vt%s_stream_tsm.csv" % vt), vt
        assert os.path.isfile(D + "/arm_vt%s_weights.csv" % vt), vt
    assert os.path.isfile(D + "/arm_vt01_stream_tsm.csv")


def test_battery_and_adopted_champion():
    lg = _log()
    assert "Champion sha16 pre-run: cfa9ec4d38158691 / weights a384d6b92e258fd5" in lg
    assert "Champion sha16 post-run: cfa9ec4d38158691 / weights a384d6b92e258fd5 (pre==post: True)" in lg
    assert "ERA PAIR (Amendment 4): A2 continuity adjudicated against prior_champion_backup 3c456aa53193eb89 / 8313bee1ad8a72fe" in lg
    assert _sha(D + "/FINDINGS_PRECOMMIT.md") == PRECOMMIT_SHA
    dp = json.load(open(D + "/gauntlet_driverpair.json"))
    assert dp["ok"] is False and dp["checks"]["weights_repro"]["ok"] is False
    assert abs(dp["checks"]["weights_repro"]["max_dev"] - 3.2485757417433092e-09) < 1e-18
    cn = json.load(open(D + "/gauntlet_canonical.json"))
    assert cn["ok"] is True
    assert cn["checks"]["weights_repro"]["max_dev"] < 1e-15
    res = ROOT + "/campaign/results"
    # ITER61 re-anchor (2026-10-12): the live champion is now the NG-block-capped book
    # (a8ed233bd0f6fd5d / 2b0f5fbc43113149); the cfa9ec4d/a384d6b9 pair this round
    # emitted lives on byte-exact as archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha(res + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") == "a8ed233bd0f6fd5d"
    assert _sha(res + "/RAWEW13v2_IS_SR_weights.csv") == "2b0f5fbc43113149"
    assert _sha(res + "/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER61_DDCON.csv") == "cfa9ec4d38158691"
    assert _sha(res + "/archive_RAWEW13v2_IS_SR_weights_SUPERSEDED_by_ITER61_DDCON.csv") == "a384d6b92e258fd5"
    assert _sha(ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv") == "c40d008ddbf7c579"
    assert os.path.isfile(ROOT + "/campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv.meta")
    bak = D + "/prior_champion_backup"
    assert _sha(bak + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") == "3c456aa53193eb89"
    assert _sha(bak + "/RAWEW13v2_IS_SR_weights.csv") == "8313bee1ad8a72fe"
    drv = open(D + "/driver_iter49.py").read()
    assert "vol_target(net.dropna(), vt_ann=vt)" in drv
    assert "build_c5ng" not in drv and "DHHNGSP" not in drv
