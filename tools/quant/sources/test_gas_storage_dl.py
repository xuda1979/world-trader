# Offline tests -- no network. Row shape mirrors a live AGSI payload (newest-first,
# string numerics, gasDayStart date field).
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gas_storage_dl as M

TODAY = dt.date(2026, 9, 11)

ROW = {"name": "EU", "code": "eu", "gasDayStart": "2026-09-09", "gasDayEnd": "2026-09-10",
       "gasInStorage": "768.3224", "consumption": "3519", "consumptionFull": "21.83",
       "injection": "2457.81", "withdrawal": "364.7", "netWithdrawal": "-2093.1",
       "workingGasVolume": "1135.9458", "full": "67.63", "status": "C", "trend": "-"}


def days(n, end=(2026, 9, 9)):
    d = dt.date(end[0], end[1], end[2])
    return sorted(d - dt.timedelta(days=i) for i in range(n))


def rows(n=400, v=50.0):
    return [(d.isoformat(), v) for d in days(n)]


def test_parse_rows_extracts_field_and_sorts():
    got = M.parse_rows([ROW], "gasInStorage")
    assert got == [("2026-09-09", 768.3224)], got
    assert M.parse_rows([ROW], "full") == [("2026-09-09", 67.63)]
    # negative netWithdrawal (net injection) must survive, not be dropped as bad
    assert M.parse_rows([ROW], "netWithdrawal") == [("2026-09-09", -2093.1)]


def test_parse_rows_skips_missing_and_nonpositive_kept():
    bad = dict(ROW)
    bad["gasDayStart"] = None
    assert M.parse_rows([bad], "full") == []
    bad2 = dict(ROW)
    bad2["full"] = ""
    assert M.parse_rows([bad2], "full") == []
    bad3 = dict(ROW)
    bad3["full"] = "n/a"
    assert M.parse_rows([bad3], "full") == []


def test_parse_rows_dedups_and_orders():
    r2 = dict(ROW)
    r2["gasDayStart"] = "2026-09-08"
    r2["full"] = "70.1"
    got = M.parse_rows([ROW, r2, dict(ROW)], "full")
    assert got == [("2026-09-08", 70.1), ("2026-09-09", 67.63)], got


def test_lint_cal_counts_calendar_days_not_business_days():
    # A clean calendar-day series must PASS -- a business-day policy would have
    # declared every weekend a hole and failed all of them.
    r = M.lint_cal(rows(400), 0.0, 100.0, TODAY, 100)
    assert r["ok"] and r["gaps"] == 0, r
    assert r["stale_days"] == 2


def test_lint_cal_rejects():
    rr = rows(400)
    dup = list(rr)
    dup[5] = dup[4]
    assert M.lint_cal(dup, 0.0, 100.0, TODAY, 2)["reason"] == "order/dupe"
    assert M.lint_cal([("2026-09-09", 120.0)], 0.0, 100.0, TODAY, 1)["reason"] == "implausible"
    assert "n<min" in M.lint_cal(rr, 0.0, 100.0, TODAY, 9999)["reason"]
    holed = [x for x in rr if x[0] not in ("2026-08-01", "2026-08-02", "2026-08-03",
                                           "2026-08-04", "2026-08-05")]
    assert M.lint_cal(holed, 0.0, 100.0, TODAY, 2)["reason"].startswith("contiguous-hole")
    old = [(d.isoformat(), 50.0) for d in days(400, end=(2026, 8, 1))]
    assert M.lint_cal(old, 0.0, 100.0, TODAY, 2)["reason"].startswith("stale=")


def test_net_withdrawal_allows_negatives():
    pts = [("2026-09-09", -2093.1), ("2026-09-08", 1500.0)]
    r = M.lint_cal(sorted(pts), -6000.0, 6000.0, TODAY, 1)
    assert r["ok"], r


def test_lint_cal_rejects_truncated_start():
    # Regression: the live EU endpoint returned 3,900 rows (2016-) on one run and
    # 5,731 (2011-) on the next, err=None both times. A truncated pull still clears
    # min_rows, so only a start-date expectation catches it.
    r = M.lint_cal(rows(400), 0.0, 100.0, TODAY, 100, expect_start="2011-01-01")
    assert r["reason"].startswith("truncated-start="), r
    assert M.lint_cal(rows(400), 0.0, 100.0, TODAY, 100, expect_start=None)["ok"]


def test_output_path_and_series_table():
    assert M.OUT.endswith(os.path.join("quant", "data", "gas_storage")), M.OUT
    assert "sources" not in M.OUT
    assert len(set(r[0] for r in M.SERIES)) == len(M.SERIES), "series names must be unique"
