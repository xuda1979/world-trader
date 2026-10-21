"""TDD tests for campaign/team/lib/manifest.py (short helper used by data agents).

Written failing-first style (RED before the helper existed), now GREEN. Pins round-trip
save/load and the fail-closed empty return.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import manifest  # noqa: E402

TMP = "/tmp/team_manifest_test"


def test_row_fields():
    r = manifest.row("fred", "DGS10", "2000-01-03", "2026-09-08", 6000, 5)
    assert r["family"] == "fred"
    assert r["max_gap_days"] == 5


def test_save_load_roundtrip():
    rows = [manifest.row("fred", "DGS10", "2000", "2026", 6000, 5),
            manifest.row("fred", "DGS2", "2000", "2026", 7000, 4)]
    path = manifest.save(f"{TMP}/m.csv", rows)
    got = manifest.load(path)
    assert len(got) == 2
    assert got[0]["symbol"] == "DGS10"
    assert got[1]["rows"] == "7000"


def test_load_missing_is_empty_list():
    # fail-closed: a missing manifest is [], never None
    assert manifest.load(f"{TMP}/nope.csv") == []
