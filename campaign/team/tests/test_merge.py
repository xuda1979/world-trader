"""TDD RED tests for DATA_MERGE lib (campaign/team/lib/merge.py).

Pins the charter contract:
- union/rows-kept join: len(panel) == union of ALL input calendars (no inner-join hole)
- ISO date normalization (sorted, deduped, DatetimeIndex)
- economic ffill bounded by max_gap_days; anything else stays NaN -> visible in gap report
- fail-closed loader (missing file/col raises, never silent empty)
- panel write: tools/quant/data/panel_<name>/<name>.csv + manifest.csv with source map
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import merge  # noqa: E402

ROOT = "/Users/daxu/software/world-trader"


def _mk(dates, vals):
    return pd.Series(vals, index=pd.DatetimeIndex(pd.to_datetime(dates)), dtype=float)


# ---- normalization ----------------------------------------------------------
def test_normalize_sorts_dedups_and_is_datetime():
    s = _mk(["2026-01-05", "2026-01-02", "2026-01-02"], [1.0, 2.0, 3.0])
    out = merge.normalize(s)
    assert list(out.index) == list(pd.to_datetime(["2026-01-02", "2026-01-05"]))
    assert list(out.values) == [3.0, 1.0]  # keep LAST on dup dates


# ---- fail-closed loader -----------------------------------------------------
def test_load_series_missing_raises():
    with pytest.raises(FileNotFoundError):
        merge.load_series("no_such_family_zzz", "NOPE.csv")


def test_load_series_real_sp500():
    s = merge.load_series("twelvedata", "SPY", col="close")
    assert s.index.is_monotonic_increasing
    assert s.index[0] >= pd.Timestamp("2006-01-01")
    assert not s.index.has_duplicates
    assert s.notna().all()
    assert str(s.index[-1].date()) >= "2026-08-01"


# ---- union join: THE charter property ---------------------------------------
def test_union_join_keeps_all_rows():
    a = _mk(["2026-01-02", "2026-01-03", "2026-01-06"], [1, 2, 3])
    b = _mk(["2026-01-03", "2026-01-07"], [10, 20])  # has a day a lacks and vice versa
    panel = merge.union_join({"a": a, "b": b})
    # union = {02,03,06} U {03,07} = {02,03,06,07} = 4 rows (NOT 3 inner, NOT 3; illegal L16 hole)
    assert len(panel) == 4
    assert set(panel.index) == set(pd.to_datetime(
        ["2026-01-02", "2026-01-03", "2026-01-06", "2026-01-07"]))


def test_union_join_no_phantom_drop_vs_union_of_calendars():
    rng = pd.bdate_range("2020-01-01", periods=300)
    a = pd.Series(np.random.default_rng(0).normal(size=300), index=rng)
    b = a.drop(rng[::3])  # b misses every 3rd day
    c = a.drop(rng[::5])
    panel = merge.union_join({"a": a, "b": b, "c": c})
    union = a.index.union(b.index).union(c.index)
    assert len(panel) == len(union)  # row count == union of calendars
    assert panel.index.equals(union)


def test_union_join_empty_raises():
    with pytest.raises(ValueError):
        merge.union_join({})


# ---- bounded economic fill + gap report -------------------------------------
def test_fill_bounded_by_max_gap():
    idx = pd.bdate_range("2026-01-01", periods=10)
    s = pd.Series(np.arange(10.0), index=idx)
    s.iloc[4:6] = np.nan  # 2-day hole -> fillable at max_gap=5
    s.iloc[0] = np.nan     # leading NaN must STAY NaN (no fake history)
    filled = merge.fill_economic(s, max_gap_days=5)
    assert filled.iloc[0] != filled.iloc[0]  # leading NaN preserved
    # the 2-day hole is filled; every position 1..end is non-NaN (ffill, not interpolate)
    assert filled.iloc[1:].notna().all(), filled.values
    assert filled.iloc[4] == 3.0 and filled.iloc[5] == 3.0  # ffill, not interpolate
    tail = filled.iloc[6:]
    assert (tail.values == np.arange(6, 10)).all()


def test_fill_respects_max_gap():
    idx = pd.bdate_range("2026-01-01", periods=10)
    s = pd.Series(np.arange(10.0), index=idx)
    s.iloc[3:8] = np.nan  # 5-session hole
    filled = merge.fill_economic(s, max_gap_days=2)
    assert filled.isna().sum() == 5  # too wide -> left NaN, disclosed not silently filled


def test_gap_report_counts():
    idx = pd.bdate_range("2026-01-01", periods=6)
    s = pd.Series([np.nan, 1, 2, np.nan, np.nan, 5], index=idx, dtype=float)
    rep = merge.gap_report(s)
    assert rep["leading_na"] == 1 and rep["trailing_na"] == 0
    assert rep["max_gap_days"] == 3 and rep["n"] == 6


# ---- panel write + manifest -------------------------------------------------
def test_write_and_read_panel(tmp_path):
    a = _mk(["2026-01-02", "2026-01-03"], [1.0, 2.0])
    b = _mk(["2026-01-03"], [9.0])
    panel = merge.union_join({"a": a, "b": b})
    panel = panel.apply(lambda c: merge.fill_economic(c, max_gap_days=5))
    src = {"a": "unit_test", "b": "unit_test"}
    outdir = merge.write_panel(str(tmp_path), "smoke", panel, src)
    assert os.path.isfile(os.path.join(outdir, "smoke.csv"))
    man = merge.read_manifest(outdir)
    assert man["panel"] == "smoke" and man["rows"] == 2
    assert set(man["columns"]) == {"a", "b"}
    assert man["sources"] == {"a": "unit_test", "b": "unit_test"}
    back = pd.read_csv(os.path.join(outdir, "smoke.csv"), parse_dates=["date"]).set_index("date")
    assert list(back.index.strftime("%Y-%m-%d")) == ["2026-01-02", "2026-01-03"]
