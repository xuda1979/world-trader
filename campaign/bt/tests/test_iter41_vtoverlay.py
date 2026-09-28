import os, hashlib

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER41_VTOVERLAY"
PC_SHA = "63b162ed42baf0c1"
CHAMP_SHA = "8559fa55ee9a3417"
WGT_SHA = "d2d11c92a98683df"
G1_SP = " " * 16
G7_SP = " " * 19


def _log():
    return open(OUT + "/driver_iter41.log").read()


def test_seal_and_champion_integrity():
    txt = _log()
    assert "sha16 " + PC_SHA + " sealed BEFORE this run" in txt
    assert ("Champion sha16 post-run: " + CHAMP_SHA + " / weights " + WGT_SHA
            + " (pre==post: True)") in txt
    pc = OUT + "/FINDINGS_PRECOMMIT.md"
    assert os.path.exists(pc)
    assert hashlib.sha256(open(pc, "rb").read()).hexdigest()[:16] == PC_SHA


def test_anchor_continuity():
    txt = _log()
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0" in txt
    assert "weights maxdev=8.327e-17" in txt
    assert "bytes   maxdev=9.996e-17" in txt
    assert "fit rows=1809" in txt
    assert "k_covered=11" in txt
    assert "IS-SR=4.198632 (continuity 4.198632)" in txt
    assert "ANCHOR A3 g=1.0 (no-overlay limit): bytes maxdev=9.996e-17" in txt
    assert "to=4.0308 bp/yr" in txt


def test_sweep_table():
    txt = _log()
    for row in ("0.04   4.206989", "0.05   4.077979", "0.06   3.933505",
                "0.07   3.849260", "0.08   3.828840"):
        assert row in txt
    assert "ADMITTED: 1 / 5" in txt


def test_reveal_and_gates():
    txt = _log()
    assert "REVEAL book: vt=0.04" in txt
    assert "FS SR=3.794703" in txt
    assert "cagr=19.0481 pct" in txt
    assert "grossmax=1.095527729" in txt
    assert "GATE 1 FS ann>=20pct" + G1_SP + "FAIL" in txt
    assert "GATE 7 OOS police" + G7_SP + "FAIL" in txt
    assert "bin 2021-22 dSR=-0.0066" in txt
    assert "ADOPTABLE" not in txt


def test_verdict_and_run1_preservation():
    txt = _log()
    assert ("VERDICT: REJECT - failed gates: 1 FS ann>=20pct, 7 OOS police"
            " (no second reveal per precommit)") in txt
    r1 = OUT + "/driver_iter41_run1_g1defect.log"
    assert os.path.exists(r1)
    t1 = open(r1).read()
    assert "GATE 1 FS ann>=20pct" + G1_SP + "PASS" in t1
    assert os.path.exists(OUT + "/candidate_vt0.04_daily.csv")
    assert os.path.exists(OUT + "/candidate_vt0.04_gpath.csv")
    assert not os.path.exists(OUT + "/candidate_vt0.04_weights.csv")


def test_d18_lineage_evidence():
    d40 = open(ROOT + "/campaign/agents/chief/coord/ITER40_DIESCRACK_L/driver_iter40.py").read()
    assert "g1 = (f_ann_c >= 0.20) or (f_ann_a >= 0.20)" in d40
    pc = open(OUT + "/FINDINGS_PRECOMMIT.md").read()
    assert "AMENDMENT 1" in pc
    assert "D18" in pc
