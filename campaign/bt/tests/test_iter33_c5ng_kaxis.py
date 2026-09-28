#@ ITER33 reality-pins (2026-09-19, session 15): the C5ng-family calm-filter scalar k.
# ITER32 closed the signal-parameter axis for a6r7 (DUR=1.9, interior IS argmax). ITER33
# sweeps the ONE frozen scalar of the LARGEST committed exposure: k=2.5 in the C5ng/C5ngsum
# generator (calm filter: flat when the absolute log-return exceeds k times trailing-90d
# sigma shift(1)); k in {1.5, 2.0, 2.5, 3.0, 3.5} SHARED across both variants per the
# sealed precommit 923220d3c57bc3e1. VERDICT: IS-SR RISES with k above the incumbent (best
# novel 4.227429 at k=3.5 = bar + 0.0288) - the FIRST axis where a novel cell genuinely
# beats the incumbent inside its own one-parameter family on IS. ONE reveal fired: FS SR
# 3.758975 above 3.751429 with ALL operator gates green, but the 5-bin OOS police reads
# 2/5 positive with a -0.2537 bin in 2021-22 (the calm filter protects the gas sleeve in
# the energy-crisis regime; IS wants to remove exactly what OOS needs) => G7 FAIL => REJECT
# per the sealed stop rule. ITER17-law kill 8. Champion byte-stable pre==post.
# Pins assert on recorded artifacts (log lines + file bytes), never on an exit code.
#@

import glob
import hashlib
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ITER33 = os.path.join(ROOT, "campaign", "agents", "chief", "coord", "ITER33_C5NG_KAXIS")
CHAMP = os.path.join(ROOT, "campaign", "results", "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
WGT = os.path.join(ROOT, "campaign", "results", "RAWEW13v2_IS_SR_weights.csv")


def _sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def _read(path):
    with open(path) as fh:
        return fh.read()


def test_champion_of_record_is_adopted_iter43_blob():
    # Re-anchored at the 2026-09-19 ITER43 adoption (A5r2 VT-axis argmax VT=0.15): the
    # live champion of record is now 3c456aa53193eb89 / weights 8313bee1ad8a72fe (ITER47 vt024 re-pin 2026-09-19; was e67446186e269b88/bde8612d0b295068 through ITER46). The
    # ITER33-era incumbent (8559fa55ee9a3417 / d2d11c92a98683df) is preserved byte-exact
    # in coord/ITER43_A5R2_VT/prior_champion_backup/ and recorded in the ITER33 memo
    # (the champion WAS byte-stable pre==post through ITER33).
    assert _sha16(CHAMP) == "cfa9ec4d38158691"
    assert _sha16(WGT) == "a384d6b92e258fd5"


def test_iter33_precommit_sealed_before_run():
    pre = os.path.join(ITER33, "FINDINGS_PRECOMMIT.md")
    logf = os.path.join(ITER33, "driver_iter33.log")
    assert os.path.exists(pre) and os.path.exists(logf)
    assert _sha16(pre) == "923220d3c57bc3e1"
    assert os.path.getmtime(pre) < os.path.getmtime(logf)
    assert "BEFORE any candidate computation" in _read(pre)


def test_iter33_anchors_exact():
    log = _read(os.path.join(ITER33, "driver_iter33.log"))
    assert "ANCHOR A1 regen k=2.5 vs saved: C5ng maxdev=9.975e-17 (n=7381)  C5ngsum maxdev=9.996e-17 (n=7381)  need <1e-12" in log
    assert "ANCHOR A2 projection-identity on incumbent: maxdev=0.0 (need exactly 0)" in log
    assert "ANCHOR A2 weights maxdev=8.327e-17 (need <1e-12)" in log
    assert "ANCHOR A2 bytes   maxdev=9.996e-17 (need <1e-12) n=4806" in log
    assert "ANCHOR A2 grossmax=1.000000000  fit rows=1809  k_covered=11" in log
    assert "ANCHOR A2 incumbent Wmax_sf(x11)=1.8115x  IS-SR=4.198632 (continuity 4.198632)" in log
    assert "ANCHOR CELL k=2.5: weights dev vs committed 2.794e-09 (need <1e-6); book dev vs champ 4.276e-10 (need <1e-9)" in log


def test_iter33_cell_table_three_admitted():
    log = _read(os.path.join(ITER33, "driver_iter33.log"))
    assert "1.50   8.896e-02  4.171476    18.002       -2.54    0/9  1.6711x  no" in log
    assert "2.00   5.683e-02  4.199543    18.176       -2.56    0/9  1.7630x  YES" in log
    assert "2.50   9.996e-17  4.198632    18.122       -2.56    0/9  1.8115x  no (anchor)" in log
    assert "3.00   7.449e-02  4.204041    18.342       -2.55    0/9  1.7852x  YES" in log
    assert "3.50   7.517e-02  4.227429    18.449       -2.56    0/9  1.8359x  YES" in log
    assert "ADMITTED: 3 / 5 (jitter tolerance 1e-4 on the IS bar)" in log
    arms = sorted(os.path.basename(f) for f in glob.glob(os.path.join(ITER33, "arm_k*_weights.csv")))
    assert arms == ["arm_k1.50_weights.csv", "arm_k2.00_weights.csv",
                    "arm_k2.50_weights.csv", "arm_k3.00_weights.csv",
                    "arm_k3.50_weights.csv"]


def test_iter33_incumbent_not_is_argmax_first_such_axis():
    log = _read(os.path.join(ITER33, "driver_iter33.log"))
    assert "3.50   7.517e-02  4.227429" in log
    assert float("4.227429") > float("4.198632") + 1e-4, "novel cell must beat the incumbent on IS for the reveal to fire"
    assert float("4.199543") > float("4.198632"), "incumbent sits in a local IS dip between k=2.0 and k=3.0"
    assert float("4.171476") < float("4.198632") - 1e-4, "k=1.5 filter-too-tight cell must sit below the bar"


def test_iter33_reveal_fired_and_rejected_on_g7_only():
    log = _read(os.path.join(ITER33, "driver_iter33.log"))
    assert "GLOBAL ARGMAX (IS-only): k=3.50 IS-SR=4.227429 Wmax_sf=1.8359x" in log
    assert "REVEAL book: 12-pool refit at k=3.50, gear 1.0, n=4806 (2008-03-31..2026-08-28)" in log
    assert "FS SR=3.758975 (incumbent 3.751429)  ann arith=21.3533 pct  cagr=23.5968 pct  MDD=-3.5676 pct  negyrs=0" in log
    assert "  GATE 1 FS ann>=20pct          PASS" in log
    assert "  GATE 2 gross<=1.6             PASS" in log
    assert "  GATE 3 FS MDD>=-7pct          PASS" in log
    assert "  GATE 4 0 FS neg yrs           PASS" in log
    assert "  GATE 5 CFX4=0                 PASS" in log
    assert "  GATE 6 Wmax_sf<=2.0x (k=11)   PASS" in log
    assert "  GATE 7 OOS police             FAIL" in log
    assert "  GATE 8 fit-window shrink<=2pct PASS" in log
    assert "  bin 2021-22 dSR=-0.2537 (cand 1.9819 vs inc 2.2356)" in log
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in log
    assert "(pre==post: True)" in log
    assert os.path.exists(os.path.join(ITER33, "candidate_k3.50_daily.csv"))
    assert os.path.exists(os.path.join(ITER33, "candidate_k3.50_weights.csv"))
