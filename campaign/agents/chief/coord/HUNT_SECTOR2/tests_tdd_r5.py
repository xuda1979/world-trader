#!/usr/bin/env python3
"""HUNT_SECTOR2 ROUND 5 TDD tests — written RED first (2026-09-08).

Round-5 charter corner: sector-rotation covariates from Nasdaq historical +
PIT-safe news/social aggregates. PIT discipline is the game: publication lag per
source documented; any series whose history cannot be proven prior -> dropped.

Tests written BEFORE the audit engine (hunt_sector2_r5.py). Run:
    python3 -m pytest tests_tdd_r5.py -q        # from repo root
"""
import sys

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2")


# ---------------------------------------------------------------- admission tests

def test_admission_module_exists_with_roster():
    """The admission audit engine must expose the pre-registered source roster."""
    import hunt_sector2_r5 as R5
    names = {e["name"] for e in R5.ROSTER}
    # Charter names GoogleNews + Reddit explicitly; Nasdaq historical is the price
    # leg; wiki_attention is the only news/social aggregate on disk with history.
    assert {"google_news", "reddit_top", "nasdaq_hist", "wiki_attention"} <= names


def test_every_source_has_documented_pit_lag():
    """V2 charter: publication lag per source documented. No empty lag strings."""
    import hunt_sector2_r5 as R5
    for e in R5.ROSTER:
        assert isinstance(e["pit_lag"], str) and len(e["pit_lag"]) > 20, e["name"]


def test_rolling_snapshot_feeds_fail_admission():
    """GoogleNews RSS / Reddit Atom are ROLLING WINDOWS with no archive (two live
    crawls 2026-09-08: GoogleNews 100 items spanning 1h-20.6d; Reddit 15-25 items
    sub-week). A series whose history cannot be proven prior is dropped per charter.
    The admission verdict must say exactly that."""
    import hunt_sector2_r5 as R5
    for src in ("google_news", "reddit_top"):
        e = R5.by_name(src)
        assert e["history_available"] is False
        assert e["admission"] == "DROP_NO_HISTORY"
        assert e["probe_window_days"] < 30.0   # both probes are sub-30-day windows


def test_nasdaq_hist_fail_admission_pre2013():
    """Nasdaq quote/historical silently ignores fromdate beyond ~10y (probed: explicit
    2000/2007 fromdate and hard 2010-2012 windows all return the same 2514 rows back
    to 2016-09; 2010-2012 window returns 0 rows). First bar 2016-09-06 > 2013-01-01
    bound -> span_class inception_fail -> not hunt-eligible."""
    import hunt_sector2_r5 as R5
    e = R5.by_name("nasdaq_hist")
    assert e["first_bar"] >= "2016-01-01"
    assert e["span_class"] == "inception_fail"
    assert e["admission"] == "DROP_INCEPTION_FAIL"


def test_wiki_attention_has_history_but_still_inception_fail():
    """wiki_attention is PIT-safe (D+1 UTC aggregation, documented) and has a real
    archive (2015-07-01..2026-09-06, 4086 rows) — but its first bar is AFTER the
    2013-01-01 inception bound -> span_class inception_fail per V2 section 9a."""
    import hunt_sector2_r5 as R5
    e = R5.by_name("wiki_attention")
    assert e["first_bar"] == "2015-07-01"
    assert e["rows"] == 4086
    assert e["history_available"] is True
    assert e["span_class"] == "inception_fail"
    assert e["admission"] == "DROP_INCEPTION_FAIL"


def test_admission_summary_counts_zero_admissible():
    """The round's honest headline: of the charter-named corner sources, how many are
    hunt-eligible? (Expected 0 -> the corner dies on data admission.)"""
    import hunt_sector2_r5 as R5
    summ = R5.admission_summary()
    assert summ["n_sources"] == len(R5.ROSTER)
    assert summ["n_admissible"] == 0
    assert summ["verdict"] == "CORNER_DEAD_ON_DATA_ADMISSION"


# ---------------------------------------------------------------- engine tests

def test_attention_sleeve_builds_and_labels_not_hunt_eligible():
    """The one still-evaluable construction (wiki_attention panel) runs the FULL V2
    battery but must carry NOT_HUNT_ELIGIBLE (V2 9a) everywhere a verdict appears."""
    import hunt_sector2_r5 as R5
    res = R5.eval_attention_sleeve()
    assert res["span_class"] == "inception_fail"
    assert res["hunt_eligible"] is False
    assert res["acceptance_track"] == "NONE_NOT_HUNT_ELIGIBLE"
    assert "NOT_HUNT_ELIGIBLE" in res["verdict"]


def test_attention_sleeve_gate_numbers_are_real_and_leak_probed():
    """The battery must actually run: gates dict with leak probe (V2 6 Step-1: explicit
    leak_check=True + sig=), a finite SR, and a non-empty decision rationale."""
    import hunt_sector2_r5 as R5
    import numpy as np
    res = R5.eval_attention_sleeve()
    g = res["gates"]
    assert np.isfinite(g["sr"])
    assert g["leak"] is not None and "leak_ok" in g          # probe ran, fail-closed
    assert g.get("beats_passive_ok") is not None             # trio judged
    assert len(res["rationale"]) > 30


def test_meta_pins_vintage_sha():
    """V2 9d/10b: every consumed file pins its sha256 + row count (A11 published
    artifact + the attention panel; XLK price is consumed only via the A11 artifact)."""
    import hunt_sector2_r5 as R5
    res = R5.eval_attention_sleeve()
    v = res["vintage_pins"]
    assert v["A11_rs_ratio#lb126k4.csv"]["sha256_16"]
    assert v["A11_rs_ratio#lb126k4.csv"]["rows"] == 2047
    assert v["wiki_attention.csv"]["sha256_16"]
    assert v["wiki_attention.csv"]["rows"] == 4086
