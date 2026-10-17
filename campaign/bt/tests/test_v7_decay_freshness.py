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
    """RE-PINNED 2026-10-17 (ITER62_REFRESH_WAVE1): the F-F 202609 CRSP vintage is NOT
    yet published (Dartmouth zip last-modified 2026-09-25 21:55Z, still the 202608
    vintage; fresh pull SHA-identical to disk, verified 2026-10-16/17). a6_r2_pair_
    residmom_fm1926 is therefore stale-by-upstream-cadence (+47d), exactly as in the
    09-25 session-1 state (pin was n_stale == 1, a6, then). All other 19 sleeves are
    fresh after the wave. Pin == 1 with the a6 name; ANY OTHER sleeve going stale
    (crossing the 35/65d gap rule) fails this test loudly. The gate stays non-vacuous
    via test_freshness_rule_arithmetic + this exact-count pin. When Dartmouth
    publishes 202609, re-emit the a6 chain and re-pin to 0 (session-2 precedent)."""
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["freshness"]["n_stale"] == 1
    assert j["freshness"]["stale_sleeves"] == ["a6_r2_pair_residmom_fm1926.csv"]


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
