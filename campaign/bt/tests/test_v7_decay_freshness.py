"""V7 DATA-FRESHNESS GATE TDD — pins the staleness rule added 2026-09-22.

Motivation (real incident, same day): 16/20 V7 sleeves silently ended before
2026-09-01 (median last row 2026-08-24) while all green gates stayed green.
The decay monitor must FAIL (non-zero exit / flagged report) when sleeve data
goes stale, so live sessions never trade on unrefreshed streams unknowingly.

Pre-committed rule (before implementation):
  STALE_DAYS = 35 calendar days (max calendar gap between last sleeve row and
  the report date). Monthly-vintage sleeves (month-stamped) use 65 days.
  A sleeve is `stale` if (report_date - last_row).days > STALE_DAYS.
  The report is RED (exit 3) if ANY sleeve with weight > 0 is stale.
"""
import json
import os
import subprocess
import sys

import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
OD = f"{ROOT}/campaign/work_backtest_oos"
MON = f"{ROOT}/campaign/work_backtest_oos/v7_oos_decay_monitor.py"


def test_freshness_fields_present_in_report():
    """The decay JSON must now carry a freshness block with per-sleeve staleness."""
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert "freshness" in j, "missing freshness block"
    fr = j["freshness"]
    assert fr["stale_days_limit"] == 35
    assert fr["monthly_stale_days_limit"] == 65
    assert "n_stale" in fr and "stale_sleeves" in fr
    assert "report_date" in fr


def test_freshness_csv_column():
    """The CSV must carry a stale flag per sleeve row."""
    df = pd.read_csv(os.path.join(OD, "V7_OOS_DECAY_REPORT.csv"))
    assert "stale" in df.columns
    assert df["stale"].dtype == bool


def test_known_stale_sleeves_flagged():
    """RE-PINNED 2026-09-25: the 2026-09-25 verified data refresh extended 6 of the 7
    then-stale sleeves (brwt7/A1/Merger/diescrack/RC/FXD1 inputs; TREASFUT inputs to
    2026-08), so the 2026-09-22 pin (n_stale >= 5, TREASFUT stale) no longer holds.
    Current reality: exactly 1 stale sleeve — a6_r2_pair_residmom_fm1926 (+56d), which
    is STRUCTURALLY blocked upstream (F-F daily factors end 2026-07-31, fetched
    2026-09-23; the library/sleeve cannot extend past the last F-F monthly stamp).
    Pin n_stale == 1 with the a6 name so (a) the gate is not vacuously green, and
    (b) any NEW staleness (a second sleeve crossing 35/65d) fails this test loudly.
    When F-F August publishes and a6 is re-emitted, re-pin to 0 (with this audit note)."""
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["freshness"]["n_stale"] == 1
    assert "a6_r2_pair_residmom_fm1926.csv" in j["freshness"]["stale_sleeves"]


def test_monitor_still_readonly_on_weights():
    with open(os.path.join(OD, "OPT_20V7_weights.csv")) as f:
        before = f.read()
    subprocess.run([sys.executable, MON], capture_output=True)
    with open(os.path.join(OD, "OPT_20V7_weights.csv")) as f:
        after = f.read()
    assert before == after


def test_freshness_rule_arithmetic():
    """Independent re-derivation: stale iff (report_date - last_row).days > 35 for
    daily sleeves (65 for monthly-stamped sleeves)."""
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    spec = open("/Users/daxu/software/world-trader/campaign/work_backtest_oos/V7_REPLICATION_SPEC.md").read()
    import re
    rows = re.findall(r"\| (\d+) \| `([^`]+)` \| ([\d.]+)% \|", spec)
    assert len(rows) == 20
    report_date = pd.Timestamp(j["freshness"]["report_date"])
    n_stale = 0
    for _, rel, _w in rows:
        p = os.path.join(ROOT, "campaign", rel)
        df = pd.read_csv(p)
        last = pd.to_datetime(df[df.columns[0]], errors="coerce").max()
        gap = (report_date - last).days
        monthly = "TREASFUT" in rel  # month-stamped vintage sleeve
        limit = 65 if monthly else 35
        if gap > limit:
            n_stale += 1
    assert j["freshness"]["n_stale"] == n_stale
