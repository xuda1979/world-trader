#!/usr/bin/env python3
"""HUNT_SECTOR2 ROUND 6 TDD tests — written RED first (2026-09-08).

Defect (found by THIS agent in R5, charter R6(a)): wt.sources.nasdaq_history
silently ignores a fromdate the API cannot serve. The Nasdaq quote/historical
endpoint caps history at ~10y (and page-limits at limit=): live probes on XLK
showed fromdate=2000 AND fromdate=2007 BOTH return exactly 2514 bars back to
2016-09-06, and hard pre-2013 windows return 0 rows. The fetcher computes
fromdate = today - (days*1.6+10), passes it in the URL, then returns whatever
came back with err=None — so a caller asking for 25y of history silently
receives 10y and any downstream span/PIT claim is wrong (this is exactly how
the R5 admission audit had to be written against a probe script instead of the
fetcher).

Fix under test: nasdaq_history must FAIL CLOSED when the served window starts
materially after the requested fromdate (fromdate ignored / truncated), and
fail closed with a DISTINCT error when the oldest served bar's date cannot be
parsed (coverage unverifiable). Healthy serves (every current caller uses
days<=400 on liquid names, far inside the cap) must pass unchanged.

Run: python3 -m pytest tests_tdd_r6.py -q    # from repo root
"""
import sys
from datetime import date, timedelta

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools")

import wt.sources as sources  # noqa: E402


def _fake_rows(dates, price=100.0):
    """Nasdaq tradesTable rows, NEWEST-FIRST (API order), dates MM/DD/YYYY."""
    rows = []
    for d in dates:
        rows.append(dict(
            date=d.strftime("%m/%d/%Y"),
            close=f"${price:.2f}", open=f"${price:.2f}",
            high=f"${price + 1:.2f}", low=f"${price - 1:.2f}",
            volume="1234567",
        ))
    return list(reversed(rows))


def _fake_payload(dates, price=100.0):
    return {"data": {"tradesTable": {"rows": _fake_rows(dates, price)}}}


def _patch_api(monkeypatch, payload):
    monkeypatch.setattr(sources, "get_json", lambda url, **kw: payload)


def _recent_bdays(periods, end=None):
    """Last `periods` business days ending at/before today."""
    end = end or (date.today() - timedelta(days=date.today().weekday() >= 5))
    return pd.bdate_range(end=end, periods=periods)


# ------------------------------------------------------------------ RED tests

def test_fromdate_ignored_beyond_cap_fails_closed():
    """THE defect: API caps ~10y and silently ignores older fromdate. A caller
    asking days=6500 (~25y) must get (None, err naming the truncation), NOT a
    2514-bar dict masquerading as the requested window."""
    served = pd.bdate_range(end="2026-09-04", periods=2514)   # first bar 2017-01
    res, err = _run_with(payload=_fake_payload(served), days=6500)
    assert res is None, f"served {len(served)} bars to {served[0].date()} for a 25y ask; err={err!r}"
    assert err and "truncat" in err.lower(), err
    assert served[0].strftime("%Y-%m-%d") in err, \
        f"err must name the served window start, got {err!r}"


def test_fromdate_ignored_beyond_cap_fails_closed_fixture(monkeypatch):
    """Same defect through the real monkeypatch fixture (the test above predates
    it and must be replaced by this one if refactored)."""
    served = pd.bdate_range(end="2026-09-04", periods=2514)
    _patch_api(monkeypatch, _fake_payload(served))
    res, err = sources.nasdaq_history("XLK", days=6500)
    assert res is None
    assert err and "truncat" in err.lower(), err
    assert served[0].strftime("%Y-%m-%d") in err, err


def test_unparseable_oldest_date_fails_closed_distinct_error(monkeypatch):
    """If the oldest served bar's date cannot be parsed, coverage cannot be
    verified -> fail closed with a DISTINCT error (not the truncation message,
    not a silent pass-through)."""
    served = _recent_bdays(60)
    payload = _fake_payload(served)
    payload["data"]["tradesTable"]["rows"][-1]["date"] = "not-a-date"  # OLDEST bar
    _patch_api(monkeypatch, payload)
    res, err = sources.nasdaq_history("SPY", days=60)
    assert res is None
    assert err and "unparseable" in err.lower(), err
    assert "truncat" not in err.lower(), err


# ------------------------------------------------------------ regression guards

def test_healthy_full_window_still_returns_data(monkeypatch):
    """Current callers (scan 60 / report 200,400 / options_rviv 90) sit far
    inside the cap. A serve that starts within the fetch cushion of the
    requested fromdate must keep returning (dict, None) with the same shape."""
    served = _recent_bdays(62)                    # ~62 bars for days=60 ask
    _patch_api(monkeypatch, _fake_payload(served))
    res, err = sources.nasdaq_history("SPY", days=60)
    assert err is None, err
    assert res is not None and len(res["close"]) == 62
    assert list(res) == ["date", "open", "high", "low", "close", "vol"]


def test_moderate_ask_far_inside_cap_passes(monkeypatch):
    """days=400 (report.py's largest ask): oldest served bar is newer than
    fromdate by the ordinary cushion-to-trading-span slack (~0.2*days+10d) and
    must NOT be flagged."""
    served = pd.bdate_range(end=date.today(), periods=400)
    _patch_api(monkeypatch, _fake_payload(served))
    res, err = sources.nasdaq_history("SPY", days=400)
    assert err is None, err
    assert len(res["close"]) == 400


# --------------------------------------------------------------------- helpers

def _run_with(payload, days):
    """Direct call path used by the first RED test (module-level patch by hand,
    restored in finally; the fixture twin covers the pytest-managed path)."""
    orig = sources.get_json
    sources.get_json = lambda url, **kw: payload
    try:
        return sources.nasdaq_history("XLK", days=days)
    finally:
        sources.get_json = orig
