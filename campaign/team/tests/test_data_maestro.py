"""DATA_MAESTRO TDD tests: the DATA_COVERAGE.md map must be GENERATED from on-disk truth,
never hand-written. Generator: campaign/team/agents/DATA_MAESTRO/build_coverage.py.
Fail-closed: every family dir with a manifest.csv must appear in the map; empty dirs must
be listed as gaps/stubs; the gap list must rank families by span + availability + decorr.
"""
import os
import re
import subprocess
import sys

import pandas as pd

TEAM = "/Users/daxu/software/world-trader/campaign/team"
DATA = "/Users/daxu/software/world-trader/tools/quant/data"
GEN = f"{TEAM}/agents/DATA_MAESTRO/build_coverage.py"
DOC = f"{TEAM}/docs/DATA_COVERAGE.md"


def _manifest_families():
    return sorted(d for d in os.listdir(DATA)
                  if os.path.isfile(f"{DATA}/{d}/manifest.csv"))


def _regen_and_read():
    r = subprocess.run([sys.executable, GEN], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"generator failed: {r.stderr[-800:]}"
    with open(DOC) as fh:
        return fh.read()


def test_generator_exists_and_runs():
    assert os.path.isfile(GEN), "MAESTRO must own a generator, not hand-edit"
    text = _regen_and_read()
    assert "DATA COVERAGE MAP" in text


def test_map_covers_every_manifest_family():
    text = _regen_and_read()
    for fam in _manifest_families():
        assert f"| {fam} " in text or f"| {fam}|" in text, f"family {fam} missing from map"


def test_map_cites_real_spans_and_lint_counts():
    text = _regen_and_read()
    # doc series count for every family must equal its on-disk manifest row count
    with open(f"{DATA}/more_cot/manifest.csv") as fh:
        n_rows = max(0, sum(1 for _ in fh) - 1)
    m = re.search(r"more_cot \| (\d+) series", text)
    assert m and int(m.group(1)) == n_rows, (
        f"more_cot must cite disk truth {n_rows}, doc says {m.group(1) if m else '?'}")
    # fail-closed: doc must carry a lint PASS/FAIL tally, not 'CLEAN-pending' hand-waves
    assert "CLEAN-pending" not in text, "stale hand-edited lint markers must be gone"


def test_map_lists_empty_stub_dirs():
    text = _regen_and_read()
    for stub in ("sec_ftd", "stooq_c5", "more_fut"):
        d = f"{DATA}/{stub}"
        if os.path.isdir(d) and not any(f.endswith(".csv")
                                        for f in os.listdir(d)):
            assert re.search(rf"{stub}.*stub|stub.*{stub}|{stub}\b.*empty|empty.*{stub}\b",
                             text, re.I), f"empty dir {stub} must be flagged"


def test_gap_list_ranked_with_evidence():
    text = _regen_and_read()
    m = re.search(r"## Gap-leaders.*?(?=\n## |\Z)", text, re.S)
    assert m, "gap list section missing"
    items = re.findall(r"^\s*\d+\.", m.group(0), re.M)
    assert len(items) >= 3, "need >=3 ranked gap candidates"
    assert re.search(r"span.*\d{4}|19\d\d|20\d\d", m.group(0)), "gaps must cite span years"


def test_assignments_table_present():
    text = _regen_and_read()
    assert re.search(r"(?i)assignment", text), "per-round data-task assignments required"
    for agent in ("DATA_PULL", "DATA_CLEAN", "DATA_ORGANIZE", "DATA_MERGE"):
        assert agent in text, f"{agent} must be assigned"


def test_inventory_is_proper_markdown_table():
    text = _regen_and_read()
    m = re.search(r"## Inventory.*?\n(\|.*?\n)\|---", text, re.S)
    assert m, "inventory table must have a header row before its |---| separator"
    header = m.group(1)
    for col in ("family", "series", "span", "lint"):
        assert col in header, f"table header missing column {col}"


def test_manifest_byproduct_rows_not_counted_as_series():
    """R1 2026-09-08: cb_rates claims 6 series on disk truth=5 data CSVs; the extra row is
    the manifest_lint.csv byproduct. Generator must not count non-data byproduct files."""
    text = _regen_and_read()
    n_disk = sum(1 for f in os.listdir(f"{DATA}/cb_rates")
                 if f.endswith(".csv") and f not in ("manifest.csv", "manifest_lint.csv"))
    m = re.search(r"\| cb_rates \| (\d+) series", text)
    assert m, "cb_rates row missing"
    assert int(m.group(1)) == n_disk, (
        f"generator counted {m.group(1)} for cb_rates, disk truth {n_disk} data CSVs")


def test_stale_unparsable_claims_never_persist():
    """R1 2026-09-08: stub manifests were normalized to header-only (47B) at 14:40 today,
    yet the old map still claimed UNPARSABLE EmptyDataError. Generator must describe the
    CURRENT on-disk state (header-only => EMPTY manifest), never stale error labels."""
    text = _regen_and_read()
    for stub in ("sec_ftd", "fiscal_tga", "stooq_c5", "more_fut"):
        m = pd.read_csv(f"{DATA}/{stub}/manifest.csv")
        if len(m) == 0:
            assert f"| {stub} " in text, f"{stub} missing from map"
            assert stub not in re.search(r"UNPARSABLE[^|]*", text).group(0), (
                f"{stub} is parseable-empty now; stale UNPARSABLE claim in map")


def test_empty_manifest_with_data_on_disk_is_flagged_not_hidden():
    """R1 2026-09-08 fail-closed: cboe_options manifest says 0 series but latest/ holds
    data CSVs (14:17 reorg, files still being restored concurrently). An empty manifest
    must NOT let on-disk data disappear from the map. NOTE: the tree mutates live (fleet
    reorganizer), so we assert the NEEDS ORGANIZE flag + a positive count, not exact
    equality of counts taken at two different instants."""
    text = _regen_and_read()
    for fam in ("cboe_options", "cboe_flow"):
        m = pd.read_csv(f"{DATA}/{fam}/manifest.csv")
        n_disk = sum(len(fs) for _, _, fs in os.walk(f"{DATA}/{fam}")
                     for f in fs if f.endswith(".csv") and not f.startswith("manifest"))
        if len(m) == 0 and n_disk > 0:
            row = re.search(rf"\| {fam} \|.*", text).group(0)
            assert re.search(r"NEEDS ORGANIZE \(\d+ CSVs on disk", row), (
                f"{fam}: empty manifest + {n_disk} on-disk CSVs must be flagged, got {row}")
            assert "0 CSVs" not in row, f"{fam} flag must carry a positive count: {row}"


def test_span_derived_from_csvs_when_manifest_has_no_dates():
    """R1 2026-09-08: the fleet-wide 14:40 manifest standard (family,file,date_col,kind,
    rows,cols,exception) DROPPED start/end columns — map showed span '?' for every family.
    Charter: 'decisions must cite the actual on-disk span'. Generator must derive span
    from the data CSVs themselves (head/tail probe), not trust manifest columns."""
    text = _regen_and_read()
    for fam, expect in (("more_fred", "19"), ("bis_eer", "1994"), ("more_cot", "20")):
        row = re.search(rf"\| {fam} \| \d+ series \| ([^|]+)\|", text)
        assert row, f"{fam} row missing"
        assert re.match(r"\d{4}-\d{2}-\d{2}\.\.\d{4}-\d{2}-\d{2}", row.group(1).strip()), (
            f"{fam} span must be real dates from CSVs, got {row.group(1)!r}")
