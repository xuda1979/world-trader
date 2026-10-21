"""TDD RED tests for aklib (DATA_AKSHARE fetch/lint/manifest helpers).

Failing-first: aklib.py does not exist yet. Pins:
  - normalization of akshare frames (Chinese cols / english cols) -> canonical
  - fail-closed lint (span>=365d, no all-NaN, gap limit, non-positive prices)
  - manifest row shape matches campaign/team/lib/manifest.py
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aklib  # noqa: E402


def test_normalize_cn_columns_ohlcv():
    df = pd.DataFrame({"日期": ["2024-01-02", "2024-01-03"],
                       "开盘价": [1.0, 2.0], "最高价": [1.5, 2.5],
                       "最低价": [0.5, 1.5], "收盘价": [1.2, 2.2],
                       "成交量": [10, 20], "持仓量": [5, 6]})
    out = aklib.normalize(df)
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume", "open_interest"]
    assert out["date"].iloc[0] == "2024-01-02"
    assert out["close"].iloc[1] == 2.2


def test_normalize_en_columns_ohlcv():
    df = pd.DataFrame({"date": ["2024-01-02"], "open": [1.0], "high": [2.0],
                       "low": [0.5], "close": [1.5], "volume": [10]})
    out = aklib.normalize(df)
    assert list(out.columns) == ["date", "open", "high", "low", "close", "volume"]


def test_lint_fail_closed_on_short_span():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=30, freq="D"),
                       "close": range(30)})
    ok, why = aklib.lint(df, min_span_days=365, max_gap_days=30)
    assert not ok and "span" in why


def test_lint_fails_on_nonpositive_price():
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=500, freq="D"),
                       "close": [1.0] * 300 + [0.0] + [1.0] * 199})
    ok, why = aklib.lint(df, min_span_days=365, max_gap_days=30)
    assert not ok and "price" in why


def test_lint_fails_on_gap_over_limit():
    d = list(pd.date_range("2020-01-01", periods=400, freq="D")) + \
        list(pd.date_range("2021-09-01", periods=200, freq="D"))
    df = pd.DataFrame({"date": d, "close": [1.0 + 0.01 * i for i in range(len(d))]})
    ok, why = aklib.lint(df, min_span_days=365, max_gap_days=30)
    assert not ok and "gap" in why


def test_lint_passes_good_series():
    df = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=500, freq="D"),
                       "close": [1.0 + i * 0.01 for i in range(500)]})
    ok, why = aklib.lint(df, min_span_days=365, max_gap_days=30)
    assert ok, why


def test_manifest_row_matches_team_lib():
    r = aklib.manifest_row("ak_commodities", "RB0", "2009-03-27", "2026-09-08", 4239, 8)
    assert r["family"] == "ak_commodities" and r["max_gap_days"] == 8
    assert r["start"] == "2009-03-27" and r["rows"] == 4239


def test_write_csv_roundtrip(tmp_path):
    df = pd.DataFrame({"date": ["2024-01-02", "2024-01-03"], "close": [1.0, 2.0]})
    p = aklib.write_csv(str(tmp_path), "SYM.csv", df)
    back = pd.read_csv(p)
    assert len(back) == 2 and back["close"].iloc[1] == 2.0
