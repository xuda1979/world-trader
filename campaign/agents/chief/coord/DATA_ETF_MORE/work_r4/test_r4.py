#!/usr/bin/env python3
"""DATA_ETF_MORE round-4 TDD tests. Written FIRST (charter: TDD first).

Round-4 problem: R1 left 10 ETFs un-fetched on start>2007-01-01. R3 already
cleared 5 of them under the coordinator waiver (HYG EWC DBE DBP USCI -> on disk,
PASS_WAIVER in manifest.csv). The 5 genuinely unfetched: EIS TUR EPHE COPX ENOR.
Round-4 job: full keyless-source rotation for those 5, fail-closed, exact probe
evidence for any FAIL.

Covers:
  T1  nasdaq_rows(): parses the newest-first, $-prefixed Nasdaq payload into an
      ascending [date, close] frame with no $ / comma residue.
  T2  nasdaq_rows(): a non-200 / empty-tradesTable response surfaces as (None,
      err-string) -- never an empty frame masquerading as "no data".
  T3  classify(): the R3 waiver boundaries are preserved (2007-01-01 is pre2007,
      2013-01-02 is inception_fail).
  T4  lint_series(): the waiver lifts ONLY the start bound -- gap/dup/jump/
      short/stale still FAIL on an otherwise-2007plus series.
  T5  write_series(): fail-closed -- an inception_fail / FAIL series must NOT
      be written to the data dir, even if a file exists at that path from an
      earlier round (write refused, existing file untouched).
  T6  write_series(): PASS/PASS_WAIVER writes are ascending + unique-dated.
  T7  ROUND4_TARGETS: the charter's 10-name list, minus the 5 already
      PASS_WAIVER on disk, is exactly the 5 this round must rotate sources for
      (guards against re-testing a cleared name or dropping one).
  T8  probe_record(): every FAIL row's evidence dict carries a non-empty url
      and a non-empty response snippet (charter: EXACT failing probe).
"""
import os
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, HERE)
sys.path.insert(0, f"{ROOT}/tools")

import r4_fetch  # the module under test


# ---------------------------------------------------------------- T1/T2 parser
NASDAQ_PAYLOAD = {
    "data": {
        "tradesTable": {
            "rows": [
                {"date": "3:00:00 PM", "close": "$28.55", "volume": "1,234,567"},
                {"date": "12/24/2026", "close": "$28.40", "volume": "999"},
                {"date": "12/23/2026", "close": "$28.10", "volume": "1,000"},
            ]
        }
    }
}


def test_t1_nasdaq_rows_parses_ascending_nodollar():
    df, err = r4_fetch.nasdaq_rows(NASDAQ_PAYLOAD)
    assert err is None
    assert list(df.columns) == ["date", "close"]
    d = df["date"].tolist()
    # newest-first input -> oldest-first output; dates must be real Timestamps
    # (lint_series needs a datetime index for gap math -- string dates would
    # make every series FAIL(read), so Timestamps are the spec here)
    assert all(isinstance(x, pd.Timestamp) for x in d)
    assert d == sorted(d), "rows must be ascending by date"
    assert [str(x.date()) for x in d] == ["2026-12-23", "2026-12-24"]
    # intraday-timestamp row (today, no parseable date) is dropped, not faked
    assert len(df) == 2
    assert df["close"].tolist() == [28.10, 28.40]


def test_t2_nasdaq_rows_empty_payload_is_error_not_empty_frame():
    for bad in ({}, {"data": {}}, {"data": {"tradesTable": {"rows": []}}}):
        df, err = r4_fetch.nasdaq_rows(bad)
        assert df is None and err, f"payload {bad} must surface an error string"


# ------------------------------------------------------- T3/T4 waiver semantics
def test_t3_classify_waiver_boundaries():
    assert r4_fetch.classify(pd.Timestamp("2007-01-01")) == "pre2007"
    assert r4_fetch.classify(pd.Timestamp("2007-01-02")) == "2007plus"
    assert r4_fetch.classify(pd.Timestamp("2013-01-01")) == "2007plus"
    assert r4_fetch.classify(pd.Timestamp("2013-01-02")) == "inception_fail"


def _frame(start, n, freq="D"):
    idx = pd.date_range(start, periods=n, freq=freq)
    return pd.DataFrame({"date": idx, "close": [100.0 + i for i in range(n)]})


def test_t4_waiver_lifts_only_start():
    # 2007plus series, clean -> PASS_WAIVER. Fixture must END near ref_end or
    # the R2 freshness gate fires before the gate under test (FAIL(stale)).
    # a true 2007plus series: starts just after the 2007-01 bound, ends near
    # ref_end (fresh), ~5k business rows (>= 250) -- clean -> PASS_WAIVER
    st, cls, _ = r4_fetch.lint_series(_frame("2007-06-01", 5040, freq="B"),
                                      ref_end=pd.Timestamp("2026-09-01"))
    assert st == "PASS_WAIVER" and cls == "2007plus"
    # same span with one 11+ day calendar gap -> FAIL(gap): waiver does not lift
    # gap. Two NON-overlapping windows, >=250 rows TOTAL or the short gate
    # fires first (gate order: short -> dup -> gap -> jumps -> stale).
    g = pd.concat([_frame("2026-01-01", 130, freq="B"),
                   _frame("2026-07-21", 130, freq="B")])
    st, _, m = r4_fetch.lint_series(g, ref_end=pd.Timestamp("2026-09-01"))
    assert st == "FAIL(gap)" and m["maxgap"] > 10, \
        f"expected gap gate, got {st} maxgap={m['maxgap']}"
    # dup dates still FAIL (260+1 rows: dup gate fires after the short gate)
    d = pd.concat([_frame("2026-01-01", 260, freq="B"),
                   _frame("2026-02-02", 1, freq="D")])
    st, _, _ = r4_fetch.lint_series(d, ref_end=pd.Timestamp("2026-09-01"))
    assert st == "FAIL(dup)"
    # >50% 1d jump still FAIL
    j = _frame("2026-01-01", 260, freq="B")
    j.loc[j.index[100], "close"] = 1000.0
    st, _, _ = r4_fetch.lint_series(j, ref_end=pd.Timestamp("2026-09-01"))
    assert st == "FAIL(jumps)"
    # stale end still FAIL: series ends > FRESH_DAYS (1187d) before ref_end.
    # 5040 rows so the short gate cannot preempt; start 2007-06-01 so the
    # class is 2007plus and stale (checked before inception) is what fires.
    s = _frame("2007-06-01", 5040, freq="B")
    st, _, _ = r4_fetch.lint_series(s, ref_end=pd.Timestamp("2030-01-01"))
    assert st == "FAIL(stale)"
    # inception_fail (post-2013 start) is still FAIL even though every other
    # gate passes -- END the fixture near ref_end so stale cannot preempt.
    st, cls, _ = r4_fetch.lint_series(_frame("2014-06-01", 3000, freq="B"),
                                      ref_end=pd.Timestamp("2026-09-01"))
    assert st == "FAIL(inception)" and cls == "inception_fail"


# ------------------------------------------------------------- T5/T6 fail-closed
def test_t5_fail_series_never_written(tmp_path):
    target = tmp_path / "ENOR.csv"
    target.write_text("date,close\n2012-01-24,10.0\n")  # pre-existing loud row
    bad = _frame("2014-06-01", 300)  # inception_fail
    wrote = r4_fetch.write_series(bad, str(target), status="FAIL(inception)")
    assert wrote == 0, "fail-closed: nothing written for a FAIL series"
    assert target.read_text() == "date,close\n2012-01-24,10.0\n", \
        "existing loud row must be untouched"


def test_t6_pass_write_ascending_unique():
    import tempfile
    p = os.path.join(tempfile.mkdtemp(), "X.csv")
    shuffled = pd.concat([_frame("2007-06-01", 150), _frame("2007-06-01", 150)])
    wrote = r4_fetch.write_series(shuffled, p, status="PASS_WAIVER")
    assert wrote == 150
    back = pd.read_csv(p)
    assert back["date"].is_monotonic_increasing
    assert not back["date"].duplicated().any()
    assert list(back.columns) == ["date", "close"]


# ------------------------------------------------------------------ T7 targets
# NOTE (round-4 close): this test guarded the PRE-round premise (exactly 5
# names already PASS_WAIVER from R3, 5 left to rotate). The rotation has now
# run (results_r4.json), so all 10 are PASS_WAIVER and the `already` assertion
# below is retired -- the completion invariant it paved the way for lives in
# test_r4_t7_done.py (all 10 pass + match disk). Targets lists are unchanged.
def test_t7_round4_targets_exact():
    charter10 = {"HYG", "EWC", "EIS", "TUR", "DBE", "EPHE", "USCI", "COPX",
                 "DBP", "ENOR"}
    assert set(r4_fetch.ROUND4_TARGETS) == charter10
    # the 5 already cleared on disk in R3 (PASS_WAIVER in manifest.csv) must not
    # be re-fetched this round
    import csv
    with open(f"{ROOT}/tools/quant/data/more_etf/manifest.csv") as f:
        status = {row["symbol"]: row["status"] for row in csv.DictReader(f)}
    already = {s for s in charter10 if status.get(s) in ("PASS", "PASS_WAIVER")}
    assert already == {"HYG", "EWC", "DBE", "DBP", "USCI"} | \
        {"EIS", "TUR", "EPHE", "COPX", "ENOR"}, \
        f"post-round cleared set drifted: {already}"
    assert set(r4_fetch.ROTATE_TARGETS) == {"EIS", "TUR", "EPHE", "COPX", "ENOR"}


# --------------------------------------------------------------- T8 probe evidence
def test_t8_probe_record_has_url_and_snippet():
    rec = r4_fetch.probe_record(
        symbol="ENOR", source="nasdaq",
        url="https://api.nasdaq.com/api/quote/ENOR/historical?assetclass=etf",
        rc=200, snippet='{"data":null,"message":""}')
    assert rec["url"] and rec["snippet"] and rec["rc"] == 200
    assert rec["symbol"] == "ENOR" and rec["source"] == "nasdaq"
