"""AUDIT_CHAMP2 ROUND 4 (b) addendum — champion-of-record PHRASING lint.

test_audit_champ2_round4.py gates a fixed LIST of legacy headline numbers; the manual
sweep this round found a second hazard class it cannot see by construction: prose that
bills a config as "CURRENT champion" / "THE ONE NUMBER YOU CAN BET" / "champion of
record" while naming anything other than the champion of record
(GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv) or the current computed headline.

Caught on 2026-09-08: GOAL100_PROGRESS.md:7 bills the 48.2% 16-pool config as
"CURRENT champion" (2026-09-01 prose, three champion generations ago).
History-path docs (FINDINGS/STANDUP/CHARTER/LOG) are exempt, per the R3 lint design.
"""
import glob
import os
import re

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
CAMPAIGN = f"{ROOT}/campaign"
CHAMP = f"{CAMPAIGN}/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# promotion phrasing that asserts a config IS the champion of record
BILLING_RE = re.compile(
    r"(?i)current champion|champion of record|one number you can bet|"
    r"number you can bet today|champion \(unchanged"
)
HISTORY_EXEMPT = re.compile(
    r"(?i)supersede|banner|stale|not current|formerly|archive|lineage|history|"
    r"prior champion|unchanged this session|was \d"
)


def _current_headline_pct():
    r = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    return float((1 + r).prod() ** (252 / len(r)) - 1) * 100


def _gated_docs():
    docs = sorted(glob.glob(f"{CAMPAIGN}/*.md") + glob.glob(f"{CAMPAIGN}/results/*.md"))
    skip = ("FINDINGS", "STANDUP", "CHARTER", "LOG_", "CHAMPION_CARD")
    return [d for d in docs if not any(s in os.path.basename(d) for s in skip)]


def _billing_hits(text):
    hits = []
    for i, line in enumerate(text.splitlines()):
        if BILLING_RE.search(line) and not HISTORY_EXEMPT.search(line):
            hits.append((i + 1, line.strip()[:110]))
    return hits


def _names_current_champion(text):
    """Doc names the champion-of-record FILE or the computed current headline."""
    cur = f"{_current_headline_pct():.2f}%"
    return "RAWEW13v2_WEIGHTED_GEAR16" in text or cur in text


def test_billing_phrasing_must_name_the_champion_of_record_or_carry_a_banner():
    offenders = {}
    for d in _gated_docs():
        text = open(d, encoding="utf-8", errors="replace").read()
        hits = _billing_hits(text)
        if hits and not _names_current_champion(text):
            offenders[os.path.relpath(d, CAMPAIGN)] = hits
    assert not offenders, (
        "DOC BILLS A CONFIG AS CURRENT CHAMPION but names neither "
        "GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv nor the computed current "
        f"headline {_current_headline_pct():.2f}% (fix: ADDITIVE banner, never delete "
        "history):\n"
        + "\n".join(f"  {k}:{ln}: {s}" for k, v in offenders.items() for ln, s in v)
    )


def test_billing_lint_has_teeth():
    fake = "# memo\n\n| x | 48.2% | CURRENT champion |\n"
    assert _billing_hits(fake), "lost the CURRENT-champion billing pattern"
    assert not _names_current_champion(fake)
    # name the COMPUTED current headline so this fixture cannot go stale on a re-emit
    ok = fake + (f"\n> SUPERSEDE: not current; champion of record is RAWEW13v2 "
                 f"({_current_headline_pct():.2f}%)\n")
    assert _names_current_champion(ok)
    hist = "GOAL100_STANDUP_iter65.md style: ## CHAMPION (UNCHANGED this session)"
    assert _billing_hits(hist) == [], "standup-history exemption broke"
