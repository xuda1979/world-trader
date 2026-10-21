import os, hashlib
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = ROOT + "/campaign/agents/chief/coord/ITER42_BRWT15_READMIT"
PC_SHA = "2b204b1a5f3f4e0c"
CHAMP_SHA = "8559fa55ee9a3417"
WGT_SHA = "d2d11c92a98683df"
G1_SP = " " * 16
G7_SP = " " * 19


def _log():
    return open(OUT + "/driver_iter42.log").read()


def test_seal_and_champion_integrity():
    txt = _log()
    assert "sha16 " + PC_SHA + " (with Amendment 1) sealed BEFORE this run" in txt
    assert ("Champion sha16 post-run: " + CHAMP_SHA + " / weights " + WGT_SHA
            + " (pre==post: True)") in txt
    pc = OUT + "/FINDINGS_PRECOMMIT.md"
    assert os.path.exists(pc)
    assert hashlib.sha256(open(pc, "rb").read()).hexdigest()[:16] == PC_SHA
    assert "AMENDMENT 1" in open(pc).read()


def test_a1_provenance():
    txt = _log()
    assert "A1 sibling recon brwt10 ok=True maxdev=9.999e-17 inner=6567" in txt
    assert "A1 sibling recon brwt7 ok=True maxdev=9.986e-17 inner=4580" in txt
    assert "A1 sibling recon brwt5 ok=True maxdev=9.996e-17 inner=4580" in txt
    assert ("A1 ii-prime overlap-calendar identical=True  regen n=6567 "
            "tail end=2026-08-28") in txt


def test_anchor_continuity():
    txt = _log()
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0" in txt
    assert "weights maxdev=8.327e-17" in txt
    assert "bytes maxdev=9.996e-17" in txt
    assert "rows=1809 k=11 Wmax_sf(x11)=1.8115x" in txt
    assert "IS-SR=4.198632 (continuity 4.198632)" in txt


def test_cell_admission_largest_is_gain_on_record():
    txt = _log()
    assert "fit rows=1809 k=12" in txt
    assert "relw15 raw=0.083992 projected=0.083992" in txt
    assert "Wmax_sf(x12)=2.0000x" in txt
    assert "IS-SR=4.294412 (bar 4.198632)" in txt
    assert "IS-MDD=-2.5796 pct" in txt
    assert "IS negyrs=0" in txt


def test_reveal_and_g7_kill():
    txt = _log()
    assert "REVEAL book: 13-pool at projected fit weights, gear 1.0, n=4806" in txt
    assert "FS SR=3.721744 (incumbent 3.751429)" in txt
    assert "cagr=23.9585 pct" in txt
    assert "MDD=-3.7569 pct" in txt
    assert "bin 2019-20 dSR=-0.1884" in txt
    assert "bin 2021-22 dSR=+0.1005" in txt
    assert "GATE 1 FS ann>=20pct" + G1_SP + "PASS" in txt
    assert "GATE 6 Wmax_sf<=2.0x (k=12)" + " " * 9 + "PASS" in txt
    assert "GATE 7 OOS police" + G7_SP + "FAIL" in txt
    assert "ADOPTABLE" not in txt


def test_verdict_and_double_bound_allocation():
    txt = _log()
    assert ("VERDICT: REJECT - failed gates: 7 OOS police"
            " (no second reveal per precommit)") in txt
    w = pd.read_csv(OUT + "/arm_13pool_weights.csv", index_col=0).iloc[:, 0]
    blk = float(w[["brwt10", "brwt7", "brwt5", "brwt15"]].sum())
    assert abs(blk - 0.30) < 1e-9, "brwt block not at the 0.30 cap"
    assert abs(float(w["C5ng"]) * 12 - 2.0) < 1e-9, "C5ng not at the 2/12 wall"
    assert float(w["CFX4"]) == 0.0
    assert os.path.exists(OUT + "/candidate_13pool_daily.csv")
    assert os.path.exists(OUT + "/candidate_13pool_weights.csv")
