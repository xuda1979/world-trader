"""D16: the canonical gauntlet (verify_champion_r3_cmd.sh) must track the CANONICAL knobs.

D15 re-anchored the r3 cmd to --shrink 0.70 --brwt-cap 0.30 at the ITER20 swap - and went
STALE one iteration later: the ITER21 gear swap moved the canonical GEAR to 1.0, the script
kept the verifier DEFAULT_GEAR=1.6, and the gauntlet started failing-closed against the
live champion (weights_repro True; byte_repro / cost_reconciliation / causality / gross all
False - measured 2026-09-19 via a /tmp probe). Fail-closed, so never a false green - but
the independent verifier path for the champion of record was BROKEN and nothing in the
suite noticed. This pin makes the script knobs travel with the builder canonical values
and runs the REAL gauntlet on the REAL committed book, in-suite, every time.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "campaign" / "scripts"))

import rawew13v2_build as B  # noqa: E402
from bt.verify_champion import verify_champion  # noqa: E402

SCRIPT = ROOT / "campaign" / "bt" / "verify_champion_r3_cmd.sh"


def _script_flag(name):
    pat = r"(?m)^\s*--" + name + r"[ =]([^\s\\]+)"
    m = re.search(pat, SCRIPT.read_text())
    assert m is not None, (
        "verify_champion_r3_cmd.sh lost --" + name + ": the canonical gauntlet no longer "
        "pins the knob the champion was adopted under (D16). Add it back, value = builder canonical.")
    return m.group(1).strip(chr(92))


def _script_sleeves():
    txt = SCRIPT.read_text()
    pairs = re.findall(r"--sleeve ([A-Za-z0-9_]+)=(\S+)", txt)
    pairs = [(n, p.strip(chr(34))) for n, p in pairs]
    assert len(pairs) >= 12, "r3 cmd sleeve map shrank: %d entries" % len(pairs)
    out = {}
    for n, p in pairs:
        if p.startswith("$ROOT/"):
            p = str(ROOT / p[len("$ROOT/"):])
        out[n] = p if p.startswith("/") else str(ROOT / p)
    return out


def test_r3_cmd_knobs_equal_builder_canonical():
    """The script gear/shrink/brwt-cap must EQUAL the builder canonical constants, so the
    next champion swap cannot silently strand the gauntlet on a stale knob again."""
    g = float(_script_flag("gear"))
    assert g == B.GEAR, ("r3 cmd --gear %s != canonical %s (D16: this is exactly how the "
                          "gauntlet broke after the ITER21 swap)" % (g, B.GEAR))
    assert float(_script_flag("shrink")) == B.SHRINK_D
    assert float(_script_flag("brwt-cap")) == B.W_BRWT_CAP
    # ITER61 (2026-10-12): the champion of record is the SEALED VINTAGE NG-block-capped
    # book. Pin the three new knobs to the builder canonicals so the NEXT swap trips
    # this test, not the record (same D16 law as gear/shrink/brwt-cap above).
    assert float(_script_flag("ng-cap")) == B.W_NG_CAP
    assert _script_flag("vintage-end") == str(B.VINTAGE_END.date())
    assert _script_flag("c5ngsum-trunc") == str(B.C5NGSUM_TRUNC.date())


def test_r3_cmd_books_are_the_committed_ones():
    txt = SCRIPT.read_text()
    assert "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv" in txt
    assert "RAWEW13v2_IS_SR_weights.csv" in txt


def test_r3_gauntlet_ok_on_the_live_champion():
    """THE check: the independent verifier, run with the script exact inputs and the
    canonical knobs, must return ok=True against the committed champion of record."""
    ok, rep = verify_champion(
        champion_csv=str(ROOT / "campaign" / "results"
                         / "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"),
        weights_csv=str(ROOT / "campaign" / "results" / "RAWEW13v2_IS_SR_weights.csv"),
        sleeve_paths=_script_sleeves(),
        rule="minsharpe", shrink=float(_script_flag("shrink")),
        brwt_cap=float(_script_flag("brwt-cap")), gear=B.GEAR,
        ng_cap=float(_script_flag("ng-cap")),
        vintage_end=_script_flag("vintage-end"),
        c5ngsum_trunc=_script_flag("c5ngsum-trunc"),
    )
    assert ok, "canonical gauntlet RED on the live champion: %s" % (rep["errors"][:4],)
