"""ITER59 OPT_20V5 adjudication (session 39, ledger #150, 2026-09-20).

The concurrent twin (PID 34185) orphaned an OPT_20V5 blend candidate in work_backtest_oos
and exited without landing it; its self-audit claimed "genuine but modest". Independent
machine-checks REJECT on six admissibility grounds (provenance, champion-overlay circularity,
selection-on-OOS, non-capital-real accounting, internal inconsistency, overfit gap) BEFORE
any performance comparison - the fake-OOS family law (09-18 OPT_V5-V7, #115). These pins
make the rejection fail-closed: the exact rejected bytes are sealed, the inadmissibility
census is RECOMPUTED from disk (not trusted from any report), and the champion pair of
record is pinned. Any rewrite of the candidate, its generator, or the champion = RED.
"""
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OD = ROOT / "campaign/work_backtest_oos"
ITER = ROOT / "campaign/agents/chief/coord/ITER59_OPT20V5_ADJUDICATION"
WEIGHTS_SHA = "7b1dd1a06585fa2f"
SOURCE_SHA = "5c8e5b659395bfc1"
FINDINGS_SHA = "e82edf14ea5bdfe9"


def _sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _weights_rows():
    with open(OD / "OPT_20V5_weights.csv") as f:
        return [(rel, float(w)) for rel, w in list(csv.reader(f))[1:]]


def _vt_bad(rel):
    m = Path(str(ROOT / "campaign" / rel)).with_suffix(".csv.meta")
    if not m.exists():
        return "NO_META"
    t = m.read_text()
    if "FAILED_NO_PROMOTION" in t or "DEAD_NOT_PROMOTED" in t:
        return "VT_BAD"
    return "ok"


def test_candidate_bytes_sealed():
    """PIN 1: the exact rejected artifact bytes - a rewritten or re-tuned candidate
    (same name, different numbers) must RED and force re-adjudication."""
    assert _sha16(OD / "OPT_20V5_weights.csv") == WEIGHTS_SHA, "OPT_20V5 weights drifted"
    assert len(_weights_rows()) == 27, "weights row count changed"


def test_inadmissible_provenance_census_recomputed():
    """PIN 2: the census is RECOMPUTED from disk per the candidate's own vt_bad rule:
    exactly 4 FAILED_NO_PROMOTION-class sleeves at >= 12.5% aggregate weight and
    9 sleeves with no provenance meta at all. Adopting around these = RED."""
    rows = _weights_rows()
    bad = [(r, w) for r, w in rows if _vt_bad(r) == "VT_BAD"]
    nometa = [r for r, w in rows if _vt_bad(r) == "NO_META"]
    assert len(bad) == 4, "vt_bad census moved: %d" % len(bad)
    assert sum(w for _, w in bad) >= 0.125, "vt_bad weight share below sealed floor"
    assert len(nometa) == 9, "no-meta census moved: %d" % len(nometa)


def test_champion_overlay_circularity():
    """PIN 3: the candidate contains an overlay-ON-the-champion sleeve (6.22%) - the
    circularity ground. Removing it from the artifact without re-adjudication = RED."""
    ov = [(r, w) for r, w in _weights_rows() if "on_CHAMP" in r]
    assert len(ov) == 1, "overlay sleeve census moved: %d" % len(ov)
    assert ov[0][0].endswith("R2_CRYPTO_a_overlay_on_CHAMP.csv")
    assert ov[0][1] > 0.06, "overlay weight no longer material"


def test_generator_source_defects_sealed():
    """PIN 4: the generator's defect set is pinned at source - the |r|>=0.5 day scrub,
    the x1.6 zero-financing leverage line, and the dead-vintage benchmark path."""
    assert _sha16(OD / "improve_v5.py") == SOURCE_SHA, "improve_v5.py drifted"
    t = (OD / "improve_v5.py").read_text()
    assert "r[r.abs()<0.5]" in t, "day-scrub defect line lost"
    assert "*12*100*1.6" in t, "zero-financing x1.6 line lost"
    assert "RAWEW15_REFRESH_CANDIDATE_daily.csv" in t, "dead-vintage benchmark path lost"


def test_reject_means_no_adoption():
    """PIN 5: REJECT means the champion pair of record is untouched and the
    adjudication record is byte-exact."""
    for rel, want in [
        ("campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv", "cfa9ec4d38158691"),
        ("campaign/results/RAWEW13v2_IS_SR_weights.csv", "a384d6b92e258fd5"),
    ]:
        got = _sha16(ROOT / rel)
        assert got == want, "champion %s moved without an adoption ledger entry" % rel
    assert _sha16(ITER / "FINDINGS.md") == FINDINGS_SHA, "adjudication record mutated"
