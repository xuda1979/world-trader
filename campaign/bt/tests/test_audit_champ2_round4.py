"""AUDIT_CHAMP2 ROUND 4 (b) — legacy-generation stale-claim lint (extends round3).

R3's lint gates only the RAWEW13v2 lineage headlines (40.84/40.88/39.85/39.69).
Round 4 found the OLDER generations still billed as current in gated docs with no
supersede banner, AND a new hazard class: docs claiming byte-exact reproducibility
for builders whose --verify now DIFFs (the 2026-09-07 costfix wave changed sleeve
files feeding every legacy builder).

Legacy generations + their promotion framings found un-bannered on 2026-09-08:
  GOAL100_CHAMPION.md     §1 V1 55.5%, §10 V2 66.0%, §13 V3 68.6/67.7%, §14 V4 70.1/68.7%
                          (§11 V2-20Y 65.1% HAS a coord banner, but only for step 3)
  GOAL100_FINAL_REPORT.md "FINAL STATE: champion BALANCED 55.5%" — no banner at all
  GOAL100_TRUTH_MEMO.md   §16 "FINAL MAXIMALLY-DEFENSIBLE" STRICTTRADE 49.4% — no banner
  GOAL100_FINAL_STATE.md  "Current trustworthy frontier (HONEST11...) 47.9%/80.5%" — no banner

Measured --verify DIFFs (AUDIT_CHAMP2 R4, 2026-09-08, from repo root):
  champion_build.py     V1 1.130e-03 / 2.069e-03 / 4.099e-03
  champion20y_build.py  V2-20Y 3.107e-03 / 6.160e-03 / 6.206e-03
  honest11_build.py     1.942e-03 / 2.247e-03 / 3.869e-03
(banner text in the docs pins these numbers; the tests below re-measure LIVE so any
future sleeve re-emit that flips a DIFF back to IDENTICAL auto-resolves test_b.)
"""
import glob
import os
import re
import subprocess
import sys

import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
CAMPAIGN = f"{ROOT}/campaign"
CHAMP = f"{CAMPAIGN}/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"

# legacy headline strings (per-generation, as they appear in docs)
LEGACY_NUMS = [
    "55.5", "62.4",          # V1 (2026-09-01 FINAL_REPORT/CHAMPION §1)
    "66.0", "65.1",          # V2 / V2-20Y (CHAMPION §10/§11)
    "68.6", "67.7",          # V3 (CHAMPION §13)
    "70.1", "68.7",          # V4 (CHAMPION §14)
    "49.4",                  # STRICTTRADE (TRUTH_MEMO §16)
    "47.9", "39.6", "80.5",  # HONEST11 / HONEST11X804 (FINAL_STATE)
]
NUM_RE = re.compile(r"(?<![\d.])(" + "|".join(re.escape(n) for n in LEGACY_NUMS) + r")(?![\d])")
# promotion framing on the line itself or within +/-3 lines
PROMO_RE = re.compile(
    r"(?i)final|current|best honest|delivered|trustworthy|maximally-defensible|"
    r"headline|frontier|champion of record|can bet|achievable"
)
# history framing exempts a line (lineage arrows, snapshots, disclosures)
HIST_RE = re.compile(
    r"(?i)archive|supersede|lineage|history|formerly|inflated|removed|as committed|"
    r"->|→|\bwas\b|prior|pre-costfix|snapshot|honest path|fell from"
)

LEGACY_BUILDERS = {
    "champion_build.py": f"{ROOT}/campaign/scripts/champion_build.py",
    "champion20y_build.py": f"{ROOT}/campaign/scripts/champion20y_build.py",
    "honest11_build.py": f"{ROOT}/campaign/scripts/honest11_build.py",
}
# docs may only claim byte-exact repro of a builder if a banner discloses its DIFF
BUILDER_RE = {name: re.compile(re.escape(name)) for name in LEGACY_BUILDERS}
REPRO_RE = re.compile(r"(?i)byte-exact|byte-for-byte|identical|9\.9e-17|dev < 1e-1[26]")
BANNER_RE = re.compile(r"(?i)suPersede|coord banner|stale-claim banner".replace("suPersede", "SUPERSEDE"))


def _gated_docs():
    docs = sorted(glob.glob(f"{CAMPAIGN}/*.md") + glob.glob(f"{CAMPAIGN}/results/*.md"))
    return [d for d in docs if not d.endswith(".pytest_cache/README.md")]


def _current_headline_pct():
    """Current champion ann_geo (campaign convention), computed from the committed CSV."""
    r = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    return float((1 + r).prod() ** (252 / len(r)) - 1) * 100


def _has_current_banner(text):
    """Doc carries a supersede/coordinator banner naming the CURRENT computed headline."""
    cur2, cur3 = f"{_current_headline_pct():.2f}%", f"{_current_headline_pct():.3f}%"
    for m in BANNER_RE.finditer(text):
        window = text[max(0, m.start() - 200): m.start() + 2000]
        if cur2 in window or cur3 in window:
            return True
    return False


def _promotion_hits(text):
    lines = text.splitlines()
    hits = []
    for i, line in enumerate(lines):
        if NUM_RE.search(line) and not HIST_RE.search(line):
            lo, hi = max(0, i - 3), min(len(lines), i + 4)
            if any(PROMO_RE.search(l) for l in lines[lo:hi]):
                hits.append((i + 1, line.strip()[:110]))
    return hits


_VERIFY_CACHE = {}


def _builder_verify_status(builder):
    """Run <builder> --verify once; return dict fname -> max dev float (empty on crash)."""
    if builder in _VERIFY_CACHE:
        return _VERIFY_CACHE[builder]
    r = subprocess.run([sys.executable, LEGACY_BUILDERS[builder], "--verify"],
                       capture_output=True, text=True, cwd=ROOT, timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    status = {}
    for line in out.splitlines():
        m = re.search(r"(GOAL100_[A-Za-z0-9_]+\.csv).*?max\|new-old\|?\s*=\s*([\d.e+-]+)", line)
        if m:
            status[m.group(1)] = float(m.group(2))
    _VERIFY_CACHE[builder] = status
    return status


def _repro_claims(text, builder):
    """(lineno, line) pairs where the doc claims reproducibility of `builder`."""
    lines = text.splitlines()
    claims = []
    for i, line in enumerate(lines):
        if not BUILDER_RE[builder].search(line):
            continue
        lo, hi = max(0, i - 4), min(len(lines), i + 5)
        window = lines[lo:hi]
        if any(REPRO_RE.search(l) for l in window):
            claims.append((i + 1, line.strip()[:110]))
    return claims


def _banner_discloses_diff(text, builder):
    """Banner text names this builder together with a DIFF disclosure."""
    for m in BANNER_RE.finditer(text):
        window = text[max(0, m.start() - 200): m.start() + 2400]
        if BUILDER_RE[builder].search(window) and re.search(r"(?i)\bDIFF\b", window):
            return True
    return False


# --------------------------------------------------------------------------- (a)


def test_a_no_gated_doc_bills_a_legacy_generation_as_current_without_banner():
    offenders = {}
    for d in _gated_docs():
        text = open(d, encoding="utf-8", errors="replace").read()
        hits = _promotion_hits(text)
        if hits and not _has_current_banner(text):
            offenders[os.path.relpath(d, CAMPAIGN)] = hits
    assert not offenders, (
        "LEGACY GENERATION billed as current with no supersede banner naming "
        f"{_current_headline_pct():.2f}% (fix: ADDITIVE banner, never delete history):\n"
        + "\n".join(f"  {k}:{ln}: {s}" for k, v in offenders.items() for ln, s in v)
    )


# --------------------------------------------------------------------------- (b)


@pytest.mark.parametrize("builder", sorted(LEGACY_BUILDERS))
def test_b_repro_claims_require_a_diff_disclosure_banner(builder):
    offenders = {}
    for d in _gated_docs():
        text = open(d, encoding="utf-8", errors="replace").read()
        claims = _repro_claims(text, builder)
        if not claims:
            continue
        status = _builder_verify_status(builder)
        if not status:
            continue  # builder verify unrunnable -> nothing to disclose against
        if any(dev > 1e-12 for dev in status.values()):
            if not _banner_discloses_diff(text, builder):
                offenders[os.path.relpath(d, CAMPAIGN)] = (
                    claims, {k: f"{v:.3e}" for k, v in status.items()})
    assert not offenders, (
        f"DOC CLAIMS byte-exact repro of {builder} but --verify DIFFs (fix: ADDITIVE "
        "banner disclosing the measured DIFFs):\n"
        + "\n".join(
            f"  {k} verify={stats}\n" + "\n".join(f"    claim {ln}: {s}" for ln, s in cl)
            for k, (cl, stats) in offenders.items())
    )


# --------------------------------------------------------------------------- teeth


def test_c_lint_has_teeth_on_synthetic_offenders():
    cur = f"{_current_headline_pct():.2f}%"
    fake = "# memo\n\n## FINAL FRONTIER\n\nDelivered: 55.5% ann.\n"
    assert _promotion_hits(fake), "lint lost the legacy-number promotion pattern"
    assert not _has_current_banner(fake)
    bannered = fake + f"\n> SUPERSEDE BANNER: superseded; current champion is {cur}\n"
    assert _has_current_banner(bannered), "banner detector cannot clear a legit banner"
    assert not HIST_RE.search("Delivered: 55.5% ann."), "history exemption became too broad"

    repro_fake = (
        "# memo\n\nSuper: run honest11_build.py --verify -> IDENTICAL.\n"
        f"> SUPERSEDE BANNER: current champion is {cur}.\n"
    )
    assert _repro_claims(repro_fake, "honest11_build.py")
    assert not _banner_discloses_diff(repro_fake, "honest11_build.py"), \
        "banner without DIFF disclosure wrongly accepted"
