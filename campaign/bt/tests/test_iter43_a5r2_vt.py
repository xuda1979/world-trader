"""ITER43 A5r2 VT-axis pins (2026-09-19 session 23): the FIRST adoption since ITER21.

Cell: per-sleeve vol-target VT on the A5r2 stream (5.52 pct book weight), grid
{0.06, 0.08, 0.10, 0.12, 0.15}, anchor 0.10 IS-bar-ineligible by construction.
IS-admitted [0.12, 0.15]; single reveal VT=0.15 -> 8/8 ADOPTABLE; canonical pair
certified by the independent gauntlet 7/7; adopted. Champion of record moved
8559fa55ee9a3417 -> e67446186e269b88 (weights d2d11c92a98683df -> bde8612d0b295068).
Run-1 (NameError) and run-2 (A2 regen fail-closed) pre-reveal events are recorded in
coord/ITER43_A5R2_VT/run_history.md; Amendment 2 (canonicalization) post-dates the
reveal, so the driver's run-time precommit assert pinned 2d9dd522e87f6088 while the
FINAL precommit file (with Amendment 2) hashes c77a81108d19b500 - both pinned here.
"""
import hashlib
import json
import os

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER43_A5R2_VT"
PC_SHA_RUN3 = "2d9dd522e87f6088"
PC_SHA_FINAL = "c77a81108d19b500"
CHAMP_SHA = "e67446186e269b88"
WGT_SHA = "bde8612d0b295068"
SLEEVE_SHA = "901eebdd3abef617"
PRIOR_CHAMP_SHA = "8559fa55ee9a3417"
PRIOR_WGT_SHA = "d2d11c92a98683df"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _log():
    return open(OUT + "/driver_iter43.log").read()


def test_seal_amendments_and_run_history():
    pc = OUT + "/FINDINGS_PRECOMMIT.md"
    assert sha16(pc) == PC_SHA_FINAL
    txt = open(pc).read()
    assert "AMENDMENT 1" in txt and "AMENDMENT 2" in txt
    assert sha16(OUT + "/FINDINGS_PRECOMMIT_as_sealed_at_run3.md") == "bf145ccb6df0f82c"
    log = _log()
    assert "sha16 " + PC_SHA_RUN3 + " sealed BEFORE this run" in log
    rh = open(OUT + "/run_history.md").read()
    assert "Run-1" in rh and "NameError" in rh and "Run-2" in rh and "FAIL-CLOSED" in rh.upper()


def test_anchor_chain():
    log = _log()
    assert "A1a anchor-vs-module maxdev=0.000e+00" in log
    assert "A1b committed-CSV recon ok=True maxdev=9.975e-17 inner=4249 committed_nonnan=4249" in log
    assert "A2 committed-frame continuity (Amendment 1 repair): projid=0.000e+00 weights maxdev=8.327e-17 bytes maxdev=9.996e-17 n=4806 rows=1809 k=11 IS-SR=4.198632" in log
    assert "A2b regen-vs-committed fit-landing jitter (Amendment 1 disclosure): weights 9.913e-09  IS-SR 7.050e-10" in log


def test_sweep_table_and_admission():
    log = _log()
    for row in ("ARM VT=0.06: rows=1809 k=11 projid=0.000e+00 IS-SR=4.188280",
                "ARM VT=0.08: rows=1809 k=11 projid=0.000e+00 IS-SR=4.194835",
                "ARM VT=0.10: rows=1809 k=11 projid=0.000e+00 IS-SR=4.198632",
                "ARM VT=0.12: rows=1809 k=11 projid=0.000e+00 IS-SR=4.201156",
                "ARM VT=0.15: rows=1809 k=11 projid=0.000e+00 IS-SR=4.203733"):
        assert row in log
    assert "IS admission: [0.12, 0.15] (bar 4.198632, anchor arm ineligible by construction)" in log


def test_reveal_and_gates():
    log = _log()
    assert "REVEAL arm VT=0.15 (IS-argmax of admitted)" in log
    assert "FS SR=3.764764 (incumbent 3.751429)" in log
    assert "cagr=23.6813 pct" in log
    assert "bin 2019-20 dSR=+0.0231" in log
    assert "bin 2023-24 dSR=-0.0134" in log
    for g in ("1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
              "5 CFX4=0", "6 Wmax_sf<=2.0x (k=11)", "7 OOS police",
              "8 fit-window shrink<=2pct"):
        assert ("GATE " + g.ljust(30) + " PASS") in log
    assert "VERDICT: ADOPTABLE (8/8)" in log
    assert ("Champion sha16 post-run: " + PRIOR_CHAMP_SHA + " / weights " + PRIOR_WGT_SHA
            + " (pre==post: True)") in log


def test_adoption_artifacts():
    res = ROOT + "/campaign/results"
    # ITER49 re-pin (2026-09-19): the champion of record moved again (tsm-vt015); the ITER43
    # vintage stays pinned at canonical_vt015_* below and in ITER47 prior_champion_backup.
    assert sha16(res + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") == "cfa9ec4d38158691"
    assert sha16(res + "/RAWEW13v2_IS_SR_weights.csv") == "a384d6b92e258fd5"
    assert sha16(OUT + "/canonical_vt015_daily.csv") == CHAMP_SHA
    assert sha16(OUT + "/canonical_vt015_weights.csv") == WGT_SHA
    sl = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt015.csv"
    assert sha16(sl) == SLEEVE_SHA and os.path.exists(sl + ".meta")
    bak = OUT + "/prior_champion_backup"
    assert sha16(bak + "/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv") == PRIOR_CHAMP_SHA
    assert sha16(bak + "/RAWEW13v2_IS_SR_weights.csv") == PRIOR_WGT_SHA
    rep = json.load(open(OUT + "/verify_candidate_canonical_session23.json"))
    assert rep["ok"] is True
    assert abs(rep["stats"]["sr"] - 3.7647642016866434) < 1e-12
    assert rep["checks"]["weights_repro"]["max_dev"] < 1e-15
    live = json.load(open(ROOT + "/campaign/agents/chief/coord/verify_champion_r3_last_session23.json"))
    assert live["ok"] is True and abs(live["stats"]["sr"] - 3.7647642016866434) < 1e-12


def test_r3_cmd_tracks_adoption():
    txt = open(ROOT + "/campaign/bt/verify_champion_r3_cmd.sh").read()
    # ITER47 re-pin: the cmd tracks the CURRENT canonical sleeve (vt024)
    assert "A5_r2_contango_rateshock__vt024.csv" in txt
    assert "--is-end 2017-01-01" in txt
    assert "ITER43" in txt
    old = ROOT + "/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv"
    assert os.path.exists(old)
    assert sha16(old) == "0316cd1afd446938"  # historical vt0.10 sleeve unchanged by the adoption
