"""ITER58 more_etf futures-ETP pool-fit cell (session 38, ledger #149, 2026-09-20).

Closure-falsification audit no.2: the reference-bucketed more_etf dir (85 ETP CSVs)
holds a futures-holding family that no current-era driver ever pool-fitted. Measured
under the sealed precommit 26794451425eb4fb: 13 candidates, ONE construction (tsmom-189
vt015 single-stream transplant), 2/13 admitted at the IS bar (UNG 4.224282, DBP
4.219268), argmax reveal FIRED on UNG and DIED on the G7 OOS police (2/5 positive bins,
FS SR 3.813340 < 3.820357) - ITER17-law kill no.12. Champion UNCHANGED. These pins make
the verdict fail-closed: a tampered log, a mutated seal, a silent champion swap, or a
reverted manifest count must all RED. Era-pin duty: manifest gains ("etf-fut-etp", [58])
and LEDGER_AXES moves 32 -> 33 in the SAME landing.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ITER = ROOT / "campaign/agents/chief/coord/ITER58_ETP_POOLFIT"
PRECOMMIT_SHA = "26794451425eb4fb"
LOG_SHA = "b449ecf3f96d374b"


def _sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def test_precommit_seal_intact():
    """PIN 1: the pre-commit seal exists and is byte-exact - the verdict is only
    valid against the construction, universe, gates, and predictions sealed
    BEFORE adjudication (incl. the A1 stale-gate amendment disclosure)."""
    p = ITER / "FINDINGS_PRECOMMIT.md"
    assert p.exists(), "precommit seal missing - fail closed"
    assert _sha16(p) == PRECOMMIT_SHA, ("precommit seal mutated: %s != %s"
                                        % (_sha16(p), PRECOMMIT_SHA))


def test_driver_log_verdict_digits():
    """PIN 2: the sealed driver log is byte-exact and carries the REJECT verdict
    with the reveal digits (UNG argmax 4.224282, FS SR 3.813340 vs 3.820357,
    G7 2/5 positive). Editing any verdict or digit is a RED."""
    p = ITER / "driver_iter58.log"
    assert p.exists(), "driver log missing - fail closed"
    assert _sha16(p) == LOG_SHA, ("driver log drifted: %s != %s" % (_sha16(p), LOG_SHA))
    t = p.read_text()
    assert "ARGMAX (ONE reveal): UNG IS-SR=4.224282" in t, "argmax line lost"
    assert "FS SR=3.813340 (incumbent 3.820357)" in t, "reveal FS digits lost"
    assert "bin 2021-22 dSR=+0.0206" in t and "bin 2019-20 dSR=-0.0361" in t, "G7 bins lost"
    assert "VERDICT: REJECT - failed gates: 7 OOS police (no second reveal per precommit)" in t, "verdict line lost"
    assert "pre==post: True" in t, "champion immutability assert lost"
    assert "weights maxdev=7.633e-17 bytes maxdev=9.991e-17 n=4806 rows=1809 k=11 IS-SR=4.218504" in t, "A2 anchor line lost"


def test_admission_structure():
    """PIN 3: the sealed admission structure - exactly 2 of 13 admitted at the IS
    bar (UNG, DBP), the pure-duplicate members at relw 0.00000 EXACTLY, the UUP
    bar-equality jitter denial, and the 5 structural late-start G8 kills."""
    p = ITER / "driver_iter58.log"
    t = p.read_text()
    assert t.count("filt=True") == 2, "admitted count != 2"
    assert t.count("filt=False") == 11, "denied count != 11"
    assert "relw=0.02211 projid=5.192e-03 rows=1809 k=12 IS-SR=4.224282" in t, "UNG row lost"
    assert "relw=0.01375 projid=8.464e-03 rows=1809 k=12 IS-SR=4.219268" in t, "DBP row lost"
    assert t.count("relw=0.00000 projid=1.068e-02") == 2, "USO/DBE exact-zero duplicates lost"
    assert "relw=0.01064" in t and "IS-SR=4.218564" in t, "UUP bar-equality row lost"
    for g in ("g8=12.825%", "g8=13.101%", "g8=30.569%", "g8=15.423%"):
        assert g in t, "late-start structural G8 kill missing: " + g
    w = _sha16(ITER / "candidate_UNG_weights.csv")
    assert w == "47333b961da560fa", "UNG argmax weights CSV drifted: " + w


def test_champion_pair_unchanged():
    """PIN 4: REJECT means NO adoption - the champion pair of record must be
    byte-exact (cfa9ec4d38158691 / a384d6b92e258fd5, SR 3.820357)."""
    for rel, want in [
        ("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "cfa9ec4d38158691"),
        ("campaign/results/RAWEW13v2_IS_SR_weights.csv", "a384d6b92e258fd5"),
    ]:
        p = ROOT / rel
        assert p.exists(), "champion %s missing" % rel
        got = _sha16(p)
        assert got == want, "champion %s moved without an adoption ledger entry" % rel


def test_manifest_records_the_new_measured_axis():
    """PIN 5 (era-pin duty): the frontier-closure manifest must carry the
    etf-fut-etp family (ITER58) and the axis count 32 -> 33 in the same landing.
    Reverting the count or dropping the family REDs the suite."""
    t = (ROOT / "campaign/bt/tests/test_frontier_closure_manifest.py").read_text()
    assert '("etf-fut-etp", [58])' in t, "manifest LEDGER lost the etf-fut-etp family"
    assert re.search(r"LEDGER_AXES\s*=\s*33\b", t), "LEDGER_AXES not moved to 33"
