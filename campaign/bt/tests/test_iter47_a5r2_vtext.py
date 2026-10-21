"""ITER47 A5r2 VT upper-edge extension pins (2026-09-19 session 27): the SECOND adoption.

Cell: VT grid {0.18, 0.21, 0.24} beyond the adopted ITER43 edge 0.15 (precommit
2aafd014c7521ebe sealed BEFORE any candidate; A1 anchors run pre-seal). IS-SR monotone
rising 4.203733 -> 4.205510 -> 4.206799 -> 4.207736; all 3 cells admitted (1e-4 margin);
single reveal VT=0.24 -> 8/8 ADOPTABLE with G7 5/5 POSITIVE bins (min +0.0111) - the first
unanimous OOS reveal on record. Canonical pair certified (weights_repro 8.327e-17); adopted.
Champion of record moved e67446186e269b88 -> 3c456aa53193eb89
(weights bde8612d0b295068 -> 8313bee1ad8a72fe; canonical A5r2 sleeve -> vt024).
ANTI-DOG-CHASE BINDING: LAST seal on the A5r2-VT family (bracket 0.06..0.24 measured;
the curve still rising at 0.24 is recorded, NOT chased).
"""
import hashlib
import json
import os

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER47_A5R2_VTEXT"
PC_SHA = "2aafd014c7521ebe"
CHAMP_SHA = "3c456aa53193eb89"
WGT_SHA = "8313bee1ad8a72fe"
SLEEVE_SHA = "7ec85336e7f7d00f"
PRIOR_CHAMP_SHA = "e67446186e269b88"
PRIOR_WGT_SHA = "bde8612d0b295068"

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def _log():
    return open(OUT + "/driver_iter47.log").read()

def test_seal_and_precommit():
    assert sha16(OUT + "/FINDINGS_PRECOMMIT.md") == PC_SHA
    txt = open(OUT + "/FINDINGS_PRECOMMIT.md").read()
    assert "ANTI-DOG-CHASE" in txt.upper() and "LAST seal" in txt
    assert "A1b regen-vt015-vs-committed-sleeve ok=True maxdev=9.996344e-17 inner=4249" in open(OUT + "/anchor_iter47_a1.log").read()

def test_anchor_chain():
    lg = _log()
    assert "A1a regen-vt010-vs-module maxdev=0.000e+00 (module n=4249, regen n=4249) need <1e-12" in lg
    assert "A1b committed-CSV recon ok=True maxdev=9.996e-17 inner=4249 committed_nonnan=4249" in lg
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=8.327e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.203733 (bar 4.203733)" in lg
    assert "A2b regen-vs-committed fit-landing jitter: weights 3.816e-09  IS-SR 5.766e-09" in lg

def test_sweep_table_and_admission():
    lg = _log()
    for row in ("ARM VT=0.15: rows=1809 k=11 projid=0.000e+00 IS-SR=4.203733",
                "ARM VT=0.18: rows=1809 k=11 projid=0.000e+00 IS-SR=4.205510",
                "ARM VT=0.21: rows=1809 k=11 projid=0.000e+00 IS-SR=4.206799",
                "ARM VT=0.24: rows=1809 k=11 projid=0.000e+00 IS-SR=4.207736"):
        assert row in lg
    assert "IS admission: [0.18, 0.21, 0.24] (bar 4.203733, anchor arm ineligible by construction)" in lg

def test_reveal_and_gates():
    lg = _log()
    assert "REVEAL arm VT=0.24 (IS-argmax of admitted), gear 1.0, n=4806 (2008-03-31..2026-08-28)" in lg
    assert "FS SR=3.784099 (incumbent 3.764764)  ann arith=21.4908 pct  cagr=23.7668 pct  MDD=-3.7012 pct  negyrs=0" in lg
    assert "bin 2019-20 dSR=+0.0320 (cand 4.0789 vs inc 4.0469)" in lg
    assert "bin 2021-22 dSR=+0.0276 (cand 2.2692 vs inc 2.2416)" in lg
    assert ("GATE " + "7 OOS police".ljust(30) + " PASS") in lg
    assert "VERDICT: ADOPTABLE (8/8) -> proceed to full battery per precommit" in lg
    assert ("Champion sha16 pre-run: " + PRIOR_CHAMP_SHA + " / weights " + PRIOR_WGT_SHA + " / precommit " + PC_SHA) in lg
    assert ("Champion sha16 post-run: " + PRIOR_CHAMP_SHA + " / weights " + PRIOR_WGT_SHA + " (pre==post: True)") in lg

def test_adoption_artifacts():
    res = ROOT + "/campaign/results"
    # ITER49 re-pin (2026-09-19): the champion of record moved again (tsm-vt015); the ITER47
    # vt024 vintage stays pinned at canonical_vt024_* via CHAMP_SHA/WGT_SHA below.
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): the champion of record is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on byte-exact
    # as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert sha16(res + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") == "a8ed233bd0f6fd5d"
    assert sha16(res + "/RAWEW13v2_IS_SR_weights.csv") == "2b0f5fbc43113149"
    assert sha16(OUT + "/canonical_vt024_daily.csv") == CHAMP_SHA
    assert sha16(OUT + "/canonical_vt024_weights.csv") == WGT_SHA
    sl = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv"
    assert sha16(sl) == SLEEVE_SHA == sha16(OUT + "/arm_vt024_stream.csv")
    assert os.path.exists(sl + ".meta")
    bak = OUT + "/prior_champion_backup"
    assert sha16(bak + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily__ITER43_vt015_prior.csv") == PRIOR_CHAMP_SHA
    assert sha16(bak + "/RAWEW13v2_IS_SR_weights__ITER43_vt015_prior.csv") == PRIOR_WGT_SHA
    rep = json.load(open(OUT + "/verify_candidate_canonical_session27.json"))
    assert rep["ok"] is True
    assert abs(rep["stats"]["sr"] - 3.7840994002149047) < 1e-12
    assert rep["checks"]["weights_repro"]["max_dev"] < 1e-15
    # battery coherence: sleeve-emit identity of the PRIOR generation too
    assert sha16(OUT + "/arm_vt015_stream.csv") == "901eebdd3abef617"

def test_r3_cmd_and_builder_track_adoption():
    cmd = open(ROOT + "/campaign/bt/verify_champion_r3_cmd.sh").read()
    assert "A5_r2_contango_rateshock__vt024.csv" in cmd
    assert "--is-end 2017-01-01" in cmd
    assert "ITER47" in cmd
    bp = open(ROOT + "/campaign/scripts/rawew13v2_build.py").read()
    assert bp.count("A5_r2_contango_rateshock__vt024.csv") == 1
    old = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"
    assert os.path.exists(old)
    assert sha16(old) == "0316cd1afd446938"  # historical vt0.10 sleeve untouched
