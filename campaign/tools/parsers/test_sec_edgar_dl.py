"""TDD tests for sec_edgar_dl (DATA_EDGAR). Uses stub fetcher — NO live HTTP in tests.

Pins: fail-closed on fetch errors, as-first-filed, cache reuse, canonical outputs
(wide CSV with `date` first column), and manifest rows (family=file-name).
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sec_edgar_dl as dl  # noqa: E402


@pytest.fixture()
def stub(monkeypatch):
    calls = {"n": 0, "bad": False}

    def fake_fetch(url):
        calls["n"] += 1
        if calls["bad"]:
            raise RuntimeError("HTTP 403 simulated")
        if "company_tickers.json" in url:
            return {"0": {"cik_str": 1, "ticker": "AAAA", "title": "Alpha"},
                    "1": {"cik_str": 2, "ticker": "BBBB", "title": "Beta"}}
        cik = url.split("CIK")[1][:10]
        facts = {str(end): float(end[:4]) * 10
                 for end in ("2005-12-31", "2006-12-31", ..., "2019-12-31")} \
            if False else {f"{y}-12-31": 100.0 * y for y in range(2004, 2025)}
        return {"units": {"USD": [
            {"end": e, "val": v, "form": "10-K", "filed": f"{e[:4]}+60d", "fp": "FY"}
            for e, v in facts.items()]}}
    return fake_fetch, calls


def test_fetch_all_builds_wide_and_manifest(stub, tmp_path):
    fake_fetch, calls = stub
    out = tmp_path / "sec_edgar"
    mrows, lint = dl.run(fake_fetch, str(out), tickers=[("AAAA", "1"), ("BBBB", "2")],
                         tags=[("revenue", "Revenues")], sleep=0, min_years=5)
    df = pd.read_csv(out / "revenues.csv")
    assert list(df.columns)[:2] == ["date", "AAAA"]
    assert len(mrows) == 1 and mrows[0]["family"] == "sec_edgar"
    assert mrows[0]["file"] == "revenue.csv"
    assert mrows[0]["kind"] == "annual-fundamentals" and lint["revenue"]["tickers"] == 2
    assert lint["revenues"]["ok"] is True


def test_fetch_error_fails_closed(stub, tmp_path, monkeypatch):
    fake_fetch, calls = stub
    calls["bad"] = True
    out = tmp_path / "sec_edgar"
    with pytest.raises(RuntimeError):
        dl.run(fake_fetch, str(out), tickers=[("AAAA", "1")], tags=[("revenue", "Revenues")],
               sleep=0, min_years=5)
    assert not (out / "revenues.csv").exists(), "no partial outputs on failure"


def test_run_never_writes_when_lint_fails(stub, tmp_path):
    fake_fetch, calls = stub
    out = tmp_path / "sec_edgar"
    with pytest.raises(RuntimeError):
        dl.run(fake_fetch, str(out), tickers=[("AAAA", "1")], tags=[("revenue", "Revenues")],
               sleep=0, min_years=40)  # impossible span -> lint must FAIL closed
    assert not (out / "revenues.csv").exists()
