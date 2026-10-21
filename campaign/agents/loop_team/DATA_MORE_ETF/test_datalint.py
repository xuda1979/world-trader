"""TDD tests for DATA_MORE_ETF fail-closed series lint. MUST fail before impl exists (RED)."""
import os, sys, csv, tempfile, textwrap
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datalint  # noqa: E402

def _w(tmp, body):
    p = os.path.join(tmp, "s.csv")
    with open(p, "w") as f:
        f.write(textwrap.dedent(body))
    return p

GOOD = """\
date,open,high,low,close,vol
2020-01-01,10,11,9,10.5,1000
2020-01-02,10.5,12,10,11.0,1100
2020-01-06,11,13,10.9,12.0,900
"""

def test_happy_path(tmp_path):
    r = datalint.lint(_w(tmp_path, GOOD))
    assert r["rows"] == 3 and r["start"] == "2020-01-01" and r["end"] == "2020-01-06"
    assert r["max_gap_days"] == 4  # 01-02 -> 01-06
    assert r["zero_ret_rows"] == 0 and r["nan_rows"] == 0

def test_missing_column_fails_closed(tmp_path):
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, "date,open,close\n2020-01-01,10,10.5\n"))

def test_descending_dates_fails(tmp_path):
    bad = "date,open,high,low,close,vol\n2020-01-02,10,11,9,10.5,1\n2020-01-01,10,11,9,10.5,1\n"
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_duplicate_date_fails(tmp_path):
    bad = ("date,open,high,low,close,vol\n2020-01-01,10,11,9,10.5,1\n"
           "2020-01-01,10,11,9,10.6,1\n")
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_nonpositive_close_fails(tmp_path):
    bad = "date,open,high,low,close,vol\n2020-01-01,10,11,9,0,1\n"
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_nan_close_fails(tmp_path):
    bad = "date,open,high,low,close,vol\n2020-01-01,10,11,9,,1\n"
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_high_lt_low_fails(tmp_path):
    bad = "date,open,high,low,close,vol\n2020-01-01,10,8,9,10.5,1\n"
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_zero_return_counted(tmp_path):
    g = ("date,open,high,low,close,vol\n2020-01-01,10,11,9,10.5,1\n"
         "2020-01-02,10,11,9,10.5,1\n2020-01-03,10,11,9,10.5,1\n")
    r = datalint.lint(_w(tmp_path, g))
    assert r["zero_ret_rows"] == 2

def test_single_row_fails(tmp_path):
    bad = "date,open,high,low,close,vol\n2020-01-01,10,11,9,10.5,1\n"
    with pytest.raises(datalint.DataLintError):
        datalint.lint(_w(tmp_path, bad))

def test_manifest_row(tmp_path):
    r = datalint.lint(_w(tmp_path, GOOD))
    row = datalint.manifest_row("SYM", r)
    assert row == {"symbol": "SYM", "start": "2020-01-01", "end": "2020-01-06",
                   "rows": 3, "max_gap_days": 4, "zero_ret_rows": 0, "status": "OK"}
