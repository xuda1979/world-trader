"""TDD tests for DATA_YFIN fetch/lint/manifest/plan (RED first, offline via tmp fixtures).

Pins the charter contract (campaign/team/charters/DATA_YFIN.md):
  - CSV schema: date,open,high,low,close,volume; ascending, unique dates;
  - lint every series (span, NaNs, gaps, plausibility) - FAIL-CLOSED;
  - manifest.csv with (symbol,start,end,rows,max_gap) - plus the canonical
    DATA_ORGANIZE 7-col schema mirrored in a separate family manifest;
  - dedupe: never fetch a symbol already under tools/quant/data/ (any family).
"""
import csv
import os
import sys

import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = "/Users/daxu/software/world-trader/tools/quant/data/yfin"
sys.path.insert(0, HERE)

yfin_dl = pytest.importorskip("yfin_dl")


def _rows(dates, close, volume=1000):
    out = []
    for i, (d, c) in enumerate(zip(dates, close)):
        out.append({"date": d, "open": round(c * 0.99, 4), "high": round(c * 1.02, 4),
                    "low": round(c * 0.98, 4), "close": c, "volume": volume + i})
    return out


def _write(tmp_path, name, rows):
    p = tmp_path / name
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "open", "high", "low", "close", "volume"])
        w.writeheader()
        w.writerows(rows)
    return str(p)


def _dates(n, start="2015-01-01"):
    return [str(x.date()) for x in pd.date_range(start, periods=n, freq="B")]


# ---------- lint_series (fail-closed lint: span/NaN/gap/plausibility) ----------

def test_lint_accepts_clean_series(tmp_path):
    n = 300
    d = _dates(n, start="2022-01-03")
    p = _write(tmp_path, "X.csv", _rows(d, [10.0 + i * 0.01 for i in range(n)]))
    res = yfin_dl.lint_series(p)
    assert res["status"] == "PASS"
    assert res["rows"] == n and res["dup_dates"] == 0 and res["zero_ret_rows"] == 0


def test_lint_flags_ohlc_violation(tmp_path):
    rows = _rows(_dates(5), [10.0] * 5)
    rows[2]["high"] = 5.0                      # high < low-level close band -> implausible OHLC
    rows[2]["low"] = 20.0                      # low > high -> hard violation
    p = _write(tmp_path, "X.csv", rows)
    res = yfin_dl.lint_series(p)
    assert res["status"] == "FAIL"
    assert res["ohlc_viol"] == 1


def test_lint_flags_duplicates(tmp_path):
    rows = _rows(_dates(5), [10.0] * 5)
    rows.append(dict(rows[-1]))                # duplicate date row
    p = _write(tmp_path, "X.csv", rows)
    res = yfin_dl.lint_series(p)
    assert res["dup_dates"] == 1
    assert res["status"] == "FAIL"


def test_lint_flags_gap(tmp_path):
    d = _dates(10)
    rows = _rows(d[:5] + d[7:], [10.0 + i for i in range(8)])   # 2-business-day hole
    p = _write(tmp_path, "X.csv", rows)
    res = yfin_dl.lint_series(p)
    assert res["max_gap"] >= 3              # >1 missing business day
    assert res["status"] == "FAIL"


def test_lint_flags_negative_price(tmp_path):
    rows = _rows(_dates(5), [10.0, 10.0, -1.0, 11.0, 12.0])
    p = _write(tmp_path, "X.csv", rows)
    res = yfin_dl.lint_series(p)
    assert res["status"] == "FAIL" and res["n_bad_px"] >= 1


def test_lint_flags_unsorted_dates(tmp_path):
    d = _dates(5)
    rows = _rows([d[1], d[0], d[2], d[3], d[4]], [10.0] * 5)
    p = _write(tmp_path, "X.csv", rows)
    res = yfin_dl.lint_series(p)
    assert res["status"] == "FAIL" and res["n_bad_px"] == 0


# ---------- normalize_frame (yfinance raw -> canonical rows) ----------

def test_normalize_flattens_yf_columns():
    import numpy as np
    idx = pd.DatetimeIndex(pd.date_range("2024-01-02", periods=3, freq="B"))
    raw = pd.DataFrame(
        [[1.0, 2.0, 0.5, 1.5, 10, 1.0]] * 3,
        columns=pd.MultiIndex.from_product(
            [["Close", "High", "Low", "Open", "Volume", "Adj Close"], ["TSM"]]),
        index=idx)
    out = yfin_dl.normalize_frame(raw, "TSM")
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume"]
    assert len(out) == 3 and float(out["close"].iloc[0]) == 1.0  # auto_adjust: Close IS adj


def test_normalize_drops_nan_and_sorts():
    idx = pd.DatetimeIndex(pd.date_range("2024-01-01", periods=4, freq="D"))
    raw = pd.DataFrame({"Open": [1, np.nan, 3, 2], "High": [2, np.nan, 4, 3],
                        "Low": [0.5, np.nan, 2.5, 1.5], "Close": [1.5, np.nan, 3.5, 2.5],
                        "Volume": [10, np.nan, 30, 20]}, index=idx)
    out = yfin_dl.normalize_frame(raw, "X")
    assert out["date"].is_monotonic_increasing
    assert len(out) == 3  # NaN day dropped


# ---------- manifest ----------

def test_manifest_rows_match_disk_and_schema(tmp_path):
    p1 = _write(tmp_path, "AAA.csv", _rows(_dates(4), [5.0] * 4))
    p2 = _write(tmp_path, "BBB.csv", _rows(_dates(6), [7.0] * 6))
    for p in (p1, p2):
        yfin_dl.lint_series(p)
    yfin_dl.write_manifest(str(tmp_path))
    with open(tmp_path / "manifest.csv") as fh:
        rows = list(csv.DictReader(fh))
    hdr = ["symbol", "start", "end", "rows", "max_gap"] + [
        c for c in ("status", "dup_dates", "zero_ret_rows", "span_class", "ohlc_viol",
                    "n_bad_px") if any(r.get(c) for r in rows)]
    assert list(rows[0].keys())[:5] == ["symbol", "start", "end", "rows", "max_gap"]
    assert len(rows) == 2
    by = {r["symbol"]: r for r in rows}
    assert by["BBB"]["rows"] == "6" and by["AAA"]["rows"] == "4"


def test_family_manifest_canonical_seven_cols(tmp_path):
    # DATA_ORGANIZE contract: family, file, date_col, kind, rows, cols, exception
    p = _write(tmp_path, "CCC.csv", _rows(_dates(4), [5.0] * 4))
    yfin_dl.write_family_manifest(str(tmp_path), "yfin")
    with open(tmp_path / "manifest.csv") as fh:
        r = csv.DictReader(fh)
        assert r.fieldnames == ["family", "file", "date_col", "kind", "rows", "cols", "exception"]
        rows = list(r)
    assert len(rows) == 1 and rows[0]["family"] == "yfin" and rows[0]["date_col"] == "date"


# ---------- dedupe / plan ----------

def test_existing_symbol_index_covers_families(tmp_path, monkeypatch):
    (tmp_path / "famA").mkdir()
    (tmp_path / "famA" / "AAPL.csv").write_text("date,x\n2020-01-01,1\n")
    (tmp_path / "famB").mkdir()
    (tmp_path / "famB" / "MSFT.csv").write_text("date,x\n2020-01-01,1\n")
    monkeypatch.setattr(yfin_dl, "DATA_ROOT", str(tmp_path))
    idx = yfin_dl.existing_index(str(tmp_path))
    assert idx == {"AAPL", "MSFT"}


def test_plan_excludes_existing_symbols(tmp_path, monkeypatch):
    (tmp_path / "twelve_big").mkdir()
    (tmp_path / "twelve_big" / "TSM.csv").write_text("date,x\n2020-01-01,1\n")
    monkeypatch.setattr(yfin_dl, "DATA_ROOT", str(tmp_path))
    plan = yfin_dl.plan_symbols(["TSM", "NEW1"], str(tmp_path))
    assert plan == ["NEW1"]


def test_writers_only_inside_yfin_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(yfin_dl, "OUT", str(tmp_path / "yfin"))
    assert yfin_dl.safe_write("AAA", [("2020-01-01", 1, 2, 0.5, 1.5, 10)]) is True
    assert (tmp_path / "yfin" / "AAA.csv").is_file()
    # path traversal must be refused
    assert yfin_dl.safe_write("../ESCAPE", [("2020-01-01", 1, 2, 0.5, 1.5, 10)]) is False
    assert not (tmp_path / "ESCAPE.csv").exists()


def test_fail_closed_lint_requires_all_metrics(tmp_path):
    p = _write(tmp_path, "X.csv", _rows(_dates(3), [1.0, 2.0, 3.0]))
    res = yfin_dl.lint_series(p)
    for k in ("symbol", "start", "end", "rows", "max_gap", "status"):
        assert k in res
