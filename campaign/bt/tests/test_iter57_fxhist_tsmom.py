"""ITER57 fx_hist G10-USD trend transplant (session 37, ledger #148, 2026-09-20).

The LAST fittable never-measured data-inventory cell (fx_hist G10-USD tsmom-189 vt015
transplant) is MEASURED: the 13-pool fit assigned it relw 0.00000 exactly and IS-SR fell
4.218504 -> 4.210033 - NO-ADMISSION, no reveal, champion UNCHANGED. These pins make the
verdict fail-closed: a tampered log, a re-tuned construction, a silent champion swap, or a
reverted manifest count must all RED. Era-pin duty (Amendments 3+4): the manifest gains
("fx-hist", [57]) and LEDGER_AXES moves 31 -> 32 in the SAME landing (chain-updated 32 -> 33 by the ITER58 etf-fut-etp landing, session 38).
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ITER = ROOT / "campaign/agents/chief/coord/ITER57_FXHIST_TSMOM"
PRECOMMIT_SHA = "3ab2baad6966b10b"
STREAM_SHA = "9f61a03317a535ef"
LOG_SHA = "7bb5c194a9d296d6"


def _sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def test_precommit_seal_intact():
    """PIN 1: the pre-commit seal exists and is byte-exact - the verdict is only
    valid against the construction that was sealed BEFORE adjudication."""
    p = ITER / "FINDINGS_PRECOMMIT.md"
    assert p.exists(), "precommit seal missing - fail closed"
    assert _sha16(p) == PRECOMMIT_SHA, ("precommit seal mutated: %s != %s"
                                        % (_sha16(p), PRECOMMIT_SHA))


def test_driver_log_verdict_digits():
    """PIN 2+3: the sealed driver log is byte-exact and carries the NO-ADMISSION
    verdict with the measured digits (relw 0.00000, IS-SR 4.210033, bar 4.218504,
    no reveal). Editing the verdict or any digit is a RED."""
    p = ITER / "driver_iter57.log"
    assert p.exists(), "driver log missing - fail closed"
    assert _sha16(p) == LOG_SHA, ("driver log drifted: %s != %s" % (_sha16(p), LOG_SHA))
    t = p.read_text()
    assert "NO-ADMISSION" in t and "no reveal" in t, "verdict line lost"
    assert "relw=0.00000" in t, "zero-weight fact lost"
    assert "IS-SR=4.210033" in t and "4.218504" in t, "adjudication digits lost"
    assert "NOT admitted" in t, "stop-rule line lost"
    assert "pre==post: True" in t, "champion immutability assert lost"


def test_stream_artifact_determinism():
    """PIN 4: the frozen candidate construction is deterministic - the landed stream
    artifact must stay byte-exact. A re-tuned recipe (any vt/MA/leg/cost change)
    changes this sha and REDs."""
    p = ITER / "sleeve_FXH9_stream.csv"
    assert p.exists(), "stream artifact missing - fail closed"
    assert _sha16(p) == STREAM_SHA, ("stream artifact drifted: %s != %s - the frozen "
                                     "construction was re-tuned without a ledger entry"
                                     % (_sha16(p), STREAM_SHA))


def test_champion_pair_unchanged():
    """PIN 5: NO-ADMISSION means NO adoption - the champion pair of record must be
    byte-exact. Re-pinned at the 2026-10-12 ITER61 adoption (a8ed233bd0f6fd5d /
    2b0f5fbc43113149; the pre-adoption cfa9ec4d/a384d6b9 pair lives on byte-exact
    as results/archive_*_SUPERSEDED_by_ITER61_DDCON.csv)."""
    for rel, want in [
        ("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "a8ed233bd0f6fd5d"),
        ("campaign/results/RAWEW13v2_IS_SR_weights.csv", "2b0f5fbc43113149"),
    ]:
        p = ROOT / rel
        assert p.exists(), "champion %s missing" % rel
        got = _sha16(p)
        assert got == want, "champion %s moved without an adoption ledger entry" % rel


def test_manifest_records_the_new_measured_axis():
    """PIN 6 (era-pin duty): the frontier-closure manifest must carry the fx-hist
    family (ITER57) and the axis count 31 -> 32 in the same landing. Reverting the
    count or dropping the family REDs the suite."""
    t = (ROOT / "campaign/bt/tests/test_frontier_closure_manifest.py").read_text()
    assert '("fx-hist", [57])' in t, "manifest LEDGER lost the fx-hist family"
    assert re.search(r"LEDGER_AXES\s*=\s*33\b", t), "LEDGER_AXES not moved to 33 (ITER58 chain)"
