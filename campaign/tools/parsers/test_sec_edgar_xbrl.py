"""TDD tests for sec_edgar_xbrl (DATA_EDGAR). Pure parsing/normalizing — no HTTP.

Fixtures are synthetic minimal XBRL companyconcept payloads (structure mirrors
https://data.sec.gov/api/xbrl/companyconcept CIK###/us-gaap/<Tag>.json).
Fail-closed: any structural anomaly -> lint FAIL, never silent drop.
"""
import pandas as pd
import pytest

from sec_edgar_xbrl import (  # noqa: E402
    derived_metrics, lint_wide, parse_concept, pick_first_filed, to_wide,
)


def concept_payload(facts):
    return {"cik": 320193, "tag": "Assets", "units": {"USD": facts}}


FA = [
    # two filings for the same FY2010 (original 10-K then a 10-K/A restatement)
    {"end": "2010-09-25", "val": 100, "form": "10-K", "filed": "2010-10-27", "fp": "FY"},
    {"end": "2010-09-25", "val": 999, "form": "10-K/A", "filed": "2011-02-01", "fp": "FY"},
    {"end": "2011-09-24", "val": 110, "form": "10-K", "filed": "2011-10-28", "fp": "FY"},
    # a quarterly fact that must be excluded in annual mode
    {"end": "2011-06-25", "val": 105, "form": "10-Q", "filed": "2011-07-20", "fp": "Q3"},
]


def test_parse_concept_annual_only():
    rows = parse_concept(concept_payload(FA), annual=True)
    assert [r["end"] for r in rows] == ["2010-09-25", "2011-09-24"]


def test_parse_concept_quarterly():
    # quarterly mode keeps ONLY 10-Q facts (10-K anchors excluded)
    rows = parse_concept(concept_payload(FA), annual=False)
    assert [r["end"] for r in rows] == ["2011-06-25"]


def test_pick_first_filed_keeps_original_not_restatement():
    rows = pick_first_filed(parse_concept(concept_payload(FA), annual=True))
    assert len(rows) == 2
    assert rows[0]["val"] == 100, "must keep as-first-filed (no restatement lookahead)"


def test_parse_concept_bad_payload_fails_closed():
    with pytest.raises((KeyError, ValueError)):
        parse_concept({"units": {}}, annual=True)


def test_to_wide_panel():
    series = {"AAPL": [("2010-09-25", 100.0), ("2011-09-24", 110.0)],
              "MSFT": [("2010-06-30", 90.0), ("2011-06-30", 95.0)]}
    df = to_wide(series)
    assert list(df.columns) == ["AAPL", "MSFT"]
    assert list(df.index) == ["2010-06-30", "2010-09-25", "2011-06-30", "2011-09-24"]
    assert df.loc["2010-09-25", "AAPL"] == 100.0
    assert pd.isna(df.loc["2010-06-30", "AAPL"])


def test_lint_wide_ok():
    series = {t: [(f"{y}-12-31", float(y)) for y in range(2009, 2020)]
              for t in ("AAPL", "MSFT")}
    ok, rep = lint_wide(to_wide(series), min_years=5)
    assert ok, rep
    assert rep["tickers"] == 2 and rep["span_years"] >= 10


def test_lint_wide_fails_on_duplicate_dates():
    df = to_wide({"AAPL": [("2010-12-31", 1.0)]})
    df2 = pd.concat([df, df.loc[["2010-12-31"]]])  # duplicate index row
    ok, rep = lint_wide(df2, min_years=1)
    assert not ok and "duplicate_dates" in rep["why"]


def test_lint_wide_fails_on_short_span():
    series = {"AAPL": [("2018-12-31", 1.0), ("2019-12-31", 2.0)]}
    ok, rep = lint_wide(to_wide(series), min_years=5)
    assert not ok and "span" in rep["why"]


def test_derived_metrics():
    f = {"revenue": 200.0, "net_income": 20.0, "assets": 500.0, "equity": 250.0}
    d = derived_metrics(f)
    assert abs(d["net_margin"] - 0.10) < 1e-9
    assert abs(d["roe"] - 0.08) < 1e-9
    assert abs(d["leverage"] - 2.0) < 1e-9


def test_derived_metrics_zero_equity_not_inf():
    f = {"revenue": 100.0, "net_income": 10.0, "assets": 100.0, "equity": 0.0}
    d = derived_metrics(f)
    assert d["leverage"] != d["leverage"] or d["leverage"] in (float("inf"),) or True
    import math
    assert math.isnan(d["leverage"]), "0/0-ish must be NaN, never inf/err"
