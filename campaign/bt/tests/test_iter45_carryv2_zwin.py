import hashlib

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER45_CARRYV2_ZWIN"
LOG = OUT + "/driver_iter45.log"


def _sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def _log():
    return open(LOG, encoding="utf-8").read()


def test_log_provenance_sealed_and_frozen_blocks():
    t = _log()
    assert "FINDINGS_PRECOMMIT.md sha16 c825c1e0477a80ff sealed BEFORE this run" in t
    assert "FROZEN-BLOCK check: fit_relw/apply_cap/project_wmax/build_book text-identical to driver_iter43.py AND driver_iter36.py" in t
    assert _sha16(OUT + "/FINDINGS_PRECOMMIT.md") == "c825c1e0477a80ff"
    assert _sha16(LOG) == "0e652e03253388af"


def test_a1_anchor_retype_full_coverage_exact():
    t = _log()
    assert "A1 anchor recon (zwin=126 re-type vs committed CSV): ok=True maxdev=9.986e-17 inner=5179 committed_nonnan=5179" in t


def test_grid_admission_edge_max_anchor_not_argmax():
    t = _log()
    assert "ARM ZWIN=63: rows=1809 k=11 projid=0.000e+00 IS-SR=4.205453 IS-MDD=-2.5526 pct negyrs=0 Wmax_sf=1.8813x grossmax=1.000000000" in t
    assert "ARM ZWIN=126: rows=1809 k=11 projid=0.000e+00 IS-SR=4.203733 IS-MDD=-2.5620 pct negyrs=0 Wmax_sf=1.8604x grossmax=1.000000000" in t
    assert "ARM ZWIN=252: rows=1809 k=11 projid=0.000e+00 IS-SR=4.200360 IS-MDD=-2.5747 pct negyrs=0 Wmax_sf=1.8418x grossmax=1.000000000" in t
    assert "IS admission: [63] (bar 4.203733, anchor arm ineligible by construction)" in t
    assert "A2b regen-vs-committed fit-landing jitter (Amendment-1-class disclosure): weights 1.067e-08  IS-SR 3.692e-09" in t


def test_a2_committed_frame_continuity_exact():
    t = _log()
    assert "A2 committed-frame continuity: projid=0.000e+00 weights maxdev=8.327e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.203733 (bar 4.203733)" in t


def test_reveal_passes_every_operator_gate_and_dies_on_g7_2of5():
    t = _log()
    assert "REVEAL arm ZWIN=63 (IS-argmax of admitted), gear 1.0, n=4806 (2008-03-31..2026-08-28)" in t
    assert "  FS SR=3.767238 (incumbent 3.764764)  ann arith=21.4428 pct  cagr=23.7066 pct  MDD=-3.6836 pct  negyrs=0" in t
    assert "  bin 2017-18 dSR=-0.0011 (cand 4.7805 vs inc 4.7817)" in t
    assert "  bin 2019-20 dSR=+0.0064 (cand 4.0533 vs inc 4.0469)" in t
    assert "  bin 2021-22 dSR=-0.0037 (cand 2.2379 vs inc 2.2416)" in t
    assert "  bin 2023-24 dSR=-0.0114 (cand 4.6720 vs inc 4.6835)" in t
    assert "  bin 2025-26 dSR=+0.0015 (cand 3.5354 vs inc 3.5339)" in t
    for gate in ("1 FS ann>=20pct", "2 gross<=1.6", "3 FS MDD>=-7pct", "4 0 FS neg yrs",
                 "5 CFX4=0", "6 Wmax_sf<=2.0x (k=11)", "8 fit-window shrink<=2pct"):
        line = [l for l in t.splitlines() if ("GATE " + gate) in l][0]
        assert line.endswith("PASS"), gate
    line7 = [l for l in t.splitlines() if "GATE 7 OOS police" in l][0]
    assert line7.endswith("FAIL")
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in t


def test_champion_bytes_stable_through_iter45():
    champ = ROOT + "/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
    wgt = ROOT + "/campaign/results/RAWEW13v2_IS_SR_weights.csv"
    # ITER61 re-pin (2026-10-12, NG-block-cap adoption): live champion is now
    # a8ed233bd0f6fd5d / 2b0f5fbc43113149; the cfa9ec4d/a384d6b9 pair lives on
    # byte-exact as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv.
    assert _sha16(champ) == "a8ed233bd0f6fd5d"
    assert _sha16(wgt) == "2b0f5fbc43113149"
    t = _log()
    assert "Champion sha16 pre-run: e67446186e269b88 / weights bde8612d0b295068" in t
    assert "Champion sha16 post-run: e67446186e269b88 / weights bde8612d0b295068 (pre==post: True)" in t
