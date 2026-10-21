"""HUNT_TREASFUT round 3(a) charter duty 2 — TRUTH20Y promotion lint (2026-09-07).

Charter: "add a lint test that FAILS if any campaign doc quotes TRUTH20Y as current
champion (RED first - a passing lint test is a fine result; show the grep evidence)".

Relationship to AUDIT_CHAMP2's test_audit_champ2_round3.py::test_a2 (do not duplicate):
a2 scans ONLY campaign/*.md + campaign/results/*.md and exempts history paths outright.
This lint sweeps EVERY .md under campaign/ (agents' FINDINGS/CHARTERs included) and
exempts a mention only if the LINE itself carries provenance/breach framing
(quarantine / not-a-champion / no-builder / breach / untracked / flagged / ...).
Rationale: TRUTH20Y is quarantined (work_r3/TRUTH20Y_QUARANTINE.md: no builder in
tree, max|recon-committed| ~3e-2, geo ann 69.09% vs 53.0 arith headline, MDD -7.88%
breaches -7%, 1 neg year) — a doc may cite it only as history with that framing.

RED evidence (2026-09-07, pre-exemption, this file's first run):
  campaign/agents/G4_detrun/FINDINGS.md:21
    "=> GOAL100 TRUTH20Y = 2006-10-02..2026-08-28 = 19.8y is the honest maximum with this pool."
  (coordinator-authored 2026-09-01, BEFORE the AUDIT_CHAMP2 R2/R3 findings; bills the
  quarantined book as current truth with zero framing). The promotion-quote class the
  charter targets, live in the tree.
"""
import glob
import os
import re

import pytest

ROOT = "/Users/daxu/software/world-trader"

# a TRUTH20Y mention is an offender if it asserts currency/prominence ...
CURRENCY = re.compile(
    r"champion|current|headline|official|canonical|honest\s+maximum|the\s+truth|"
    r"is\s+the\s+(real\s+)?(max|best|goal)|\bgoal\b",
    re.I,
)
# ... unless the SAME line frames it as quarantined history
FRAME = re.compile(
    r"quarantine|provenance|not\s+a\s+champion|no\s+builder|builder\s+absent|absent\s+from"
    r"(\s+the)?\s+tree|breach|untracked|unreproduc|unquot|external|legacy|flag|"
    r"archive|supersede|do\s+not\s+(promote|quote|integrate)|ask\s+user|ignore|"
    r"reconstruct|reproduc|max\s*dev|1e-12",
    re.I,
)
# ... or is a META line about this lint itself (charters/tests describing the rule are
# self-describing, not promotions): lint machinery / RED-first evidence / quotes-of-the-rule
META = re.compile(
    r"\blint\b|\bgrep\b|tdd|red\b|red[- ]first|quotes?\s+(go100_)?truth20y|"
    r"as\s+current\s+champion|test_",
    re.I,
)
# doc-level QUARANTINE banner (campaign SUPERSEDE-banner convention, additive prepend-only):
# a doc carrying a banner naming TRUTH20Y + quarantine/provenance is already framed; its
# promotion-shaped lines are exempt at DOC level, mirroring AUDIT_CHAMP2 round-3 rule 1.
BANNER = re.compile(
    r"(quarantine|provenance)[^\n]{0,200}TRUTH20Y|TRUTH20Y[^\n]{0,200}(quarantine|provenance)",
    re.I,
)


def _offender_lines(text):
    return [
        (i, ln.strip())
        for i, ln in enumerate(text.splitlines(), 1)
        if "TRUTH20Y" in ln
        and CURRENCY.search(ln)
        and not FRAME.search(ln)
        and not META.search(ln)
    ]


def _has_quarantine_banner(text):
    return bool(BANNER.search(text))


def _all_campaign_mds():
    return sorted(glob.glob(f"{ROOT}/campaign/**/*.md", recursive=True))


def test_classifier_catches_promotion_quotes_and_only_them():
    """Teeth: the exact live hazard wording (and variants) must RED; framed lines must not."""
    assert _offender_lines(
        "=> GOAL100 TRUTH20Y = 2006-10-02..2026-08-28 = 19.8y is the honest maximum with this pool.")
    assert _offender_lines("TRUTH20Y is our current champion at 53% ann.")
    assert _offender_lines("headline: GOAL100_TRUTH20Y_BALANCED ann 53.0 (goal100 truth)")
    for framed in [
        "TRUTH20Y quarantined: no builder in tree, maxdev 3.9e-2, MDD -7.88% breach.",
        "(c) PROVENANCE: GOAL100_TRUTH20Y files are untracked (Sep 1 mtime).",
        "* TRUTH20Y (AUDIT_CHAMP2 finding: builder absent from tree, breaches MDD wall).",
        "TRUTH20Y files remain UNQUOTED as champion (AUDIT_CHAMP2 R2 pin: unreproducible).",
        "GOAL100_TRUTH20Y* (Sep 1, pre-fleet, untracked) - ask user: integrate, archive, or ignore.",
    ]:
        assert not _offender_lines(framed), framed
    # meta/self-describing lines (the lint rule itself) must not trip the lint
    for meta in [
        "(a) Stale-claim lint (TDD): grep campaign docs for 40.84 quoted as CURRENT headline and TRUTH20Y",
        "FAILS if any campaign doc quotes TRUTH20Y as current champion (RED first).",
        "doc quotes GOAL100_TRUTH20Y as current champion. RED evidence captured in",
        "campaign/bt/tests/test_treasfut_r3_truth20y_lint.py sweeps all campaign .md",
    ]:
        assert not _offender_lines(meta), meta


def test_no_campaign_doc_quotes_truth20y_as_current_champion():
    """Whole-tree sweep. LIVE OFFENDER on first run (RED): G4_detrun/FINDINGS.md:21.

    Doc-level escape: a QUARANTINE/PROVENANCE banner naming TRUTH20Y exempts the doc
    (banner convention: additive prepend, history not rewritten)."""
    offenders = {}
    for d in _all_campaign_mds():
        text = open(d, encoding="utf-8", errors="replace").read()
        if _has_quarantine_banner(text):
            continue
        hits = _offender_lines(text)
        if hits:
            offenders[os.path.relpath(d, ROOT)] = hits
    assert not offenders, (
        "TRUTH20Y quoted as current champion/truth without provenance framing "
        f"(quarantine: campaign/agents/chief/coord/HUNT_TREASFUT/work_r3/"
        "TRUTH20Y_QUARANTINE.md):\n"
        + "\n".join(f"  {k}:{i}: {s}" for k, v in offenders.items() for i, s in v)
    )


def test_g4_detrun_promotion_line_is_now_banner_exempt_or_fixed():
    """The specific 2026-09-01 G4_detrun line may no longer stand bare: the file must
    either carry a quarantine banner (additive prepend) or the line must be framed."""
    p = f"{ROOT}/campaign/agents/G4_detrun/FINDINGS.md"
    text = open(p, encoding="utf-8", errors="replace").read()
    assert _has_quarantine_banner(text) or not _offender_lines(text), (
        "G4_detrun/FINDINGS.md still bills quarantined TRUTH20Y as 'the honest maximum' "
        "with no quarantine banner and no framing on the line itself."
    )
