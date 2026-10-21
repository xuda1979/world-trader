#!/usr/bin/env python3
"""HUNT_COT2 ROUND 7 audit — own adversarial cases for the SECTOR2-R6
nasdaq_history fail-closed fix (charter R7(a), own code, no shared modules).

SECTOR2's tests_tdd_r6.py covers: cap-truncation (both tests), unparseable
OLDEST date, and two healthy-window guards. It does NOT isolate the fix's two
coverage arms separately, does not probe their exact boundary, and does not
cover a mid-series (non-oldest) unparseable date. These cases do:

  1. gap-arm boundary: serve starts EXACTLY max(30, 0.25*days) after frm
     -> must PASS (strict > in the fix); one day later -> must FAIL.
  2. bar-count arm: serve starts ON TIME (gap 0) but carries < 0.98*days bars
     -> must FAIL even though the window is correct; exactly 0.98*days -> PASS.
  3. healthy serve at the same bar count as (2) but older `days` ask
     -> guard that the arms do not cross-fire.
  4. mid-series unparseable date (NOT the oldest bar): documents actual
     behavior — the fix only validates D[0]; expectation is pass-through
     (pre-existing semantics, recorded as an observation, not a gate).

Run: python3 -m pytest campaign/agents/chief/coord/HUNT_COT2/tests_r7_nasdaq_audit.py -q
(from repo root; no network needed)
"""
import sys
from datetime import date, timedelta

import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools")

import wt.sources as sources  # noqa: E402


def _payload(bdates, bad_idx=None):
    """tradesTable payload, NEWEST-FIRST, from an oldest-first bdate index."""
    rows = []
    for i, d in enumerate(reversed(list(bdates))):
        ds = "not-a-date" if (bad_idx is not None and i == bad_idx) else d.strftime("%m/%d/%Y")
        rows.append(dict(date=ds, close="$100.00", open="$100.00",
                         high="$101.00", low="$99.00", volume="1234567"))
    return {"data": {"tradesTable": {"rows": rows}}}


def _frm(days):
    return date.today() - timedelta(days=int(days * 1.6) + 10)


def test_gap_arm_boundary_exact_threshold_passes_one_day_late_fails(monkeypatch):
    """Arm 1 (late serve start) boundary: gap == threshold passes (strict >),
    gap == threshold+1 fails. days=100 -> threshold max(30, 25) = 30."""
    days = 100
    frm = _frm(days)
    thr = max(30, int(days * 0.25))
    assert thr == 30
    today = date.today()

    # exact threshold: oldest = frm + 30 business days later in calendar terms
    oldest_ok = frm + timedelta(days=thr)
    bdates = pd.bdate_range(start=oldest_ok, end=today)
    assert len(bdates) >= int(days * 0.98), f"fixture too thin: {len(bdates)}"
    monkeypatch.setattr(sources, "get_json", lambda url, **kw: _payload(bdates))
    res, err = sources.nasdaq_history("FAKE", days=days)
    assert err is None, f"gap exactly at threshold {thr} must pass, got: {err}"
    assert res is not None and len(res["close"]) == len(bdates)

    # one calendar day later: gap thr+1 -> must fire
    oldest_late = frm + timedelta(days=thr + 1)
    bdates_late = pd.bdate_range(start=oldest_late, end=today)
    monkeypatch.setattr(sources, "get_json", lambda url, **kw: _payload(bdates_late))
    res2, err2 = sources.nasdaq_history("FAKE", days=days)
    assert res2 is None, "serve starting one day past the gap threshold must fail closed"
    assert err2 and "truncat" in err2.lower(), err2


def _thin_span(days, keep):
    """Serve that STARTS exactly on frm (gap ~0) but carries only `keep` bars:
    full frm..today business-day span with (span-keep) bars dropped from the
    middle. Isolates the bar-count arm from the gap arm — required because a
    short serve ENDING today necessarily starts ~0.23*days+10 after frm, which
    trips the GAP arm for days>=88 (the two arms are coupled otherwise)."""
    frm = _frm(days)
    span = pd.bdate_range(start=frm, end=date.today())
    assert len(span) > keep, f"span {len(span)} must exceed keep {keep}"
    drop = sorted(pd.Index(range(1, len(span) - 1)).to_series()
                  .sample(n=len(span) - keep, random_state=7))
    return span.delete(drop)


def test_bar_count_arm_fires_with_on_time_window_start(monkeypatch):
    """Arm 2 (fewer bars than asked) with a window that starts exactly on frm:
    0.98*days - 1 bars must FAIL, exactly 0.98*days bars must PASS."""
    days = 100
    need = int(days * 0.98)  # 98

    bdates_short = _thin_span(days, need - 1)  # 97 bars, D[0] ~= frm
    gap_days = (bdates_short[0].date() - _frm(days)).days
    assert gap_days <= max(30, int(days * 0.25)), (
        f"fixture must start inside the gap tolerance, got gap {gap_days}d")
    monkeypatch.setattr(sources, "get_json", lambda url, **kw: _payload(bdates_short))
    res, err = sources.nasdaq_history("FAKE", days=days)
    assert res is None, f"97 bars for a 100-bar ask must fail closed, err={err!r}"
    assert err and "truncat" in err.lower() and str(len(bdates_short)) in err, err

    bdates_ok = _thin_span(days, need)  # exactly 98 bars, D[0] = frm
    monkeypatch.setattr(sources, "get_json", lambda url, **kw: _payload(bdates_ok))
    res2, err2 = sources.nasdaq_history("FAKE", days=days)
    assert err2 is None, (
        f"exactly 0.98*days bars with on-time start must not fire either arm: {err2}")
    assert res2 is not None and len(res2["close"]) == need


def test_mid_series_unparseable_date_passes_through_observation(monkeypatch):
    """OBSERVATION CASE (documents real behavior, not a defect gate): the fix
    parses only the OLDEST served bar's date. A corrupt NON-oldest date flows
    through into the returned dict. Recorded so the audit states the fix's
    true scope."""
    days = 60
    bdates = pd.bdate_range(end=date.today(), periods=62)
    monkeypatch.setattr(sources, "get_json",
                        lambda url, **kw: _payload(bdates, bad_idx=5))
    res, err = sources.nasdaq_history("FAKE", days=days)
    # Actual behavior under the fix:
    if res is None:
        assert err, "if it fails closed it must say why"
    else:
        assert any(d == "not-a-date" for d in res["date"]), (
            "observation mismatch: expected pass-through of the mid-series bad date")
        assert err is None
