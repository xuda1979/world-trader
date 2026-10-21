#!/usr/bin/env python3
"""Round-3 integrity tests, written AFTER the round-3 charter work surfaced two
on-disk defects the R2-era lint did not catch. These tests FAIL right now (TDD
red) and pin the fixes:

  I1  every csv in more_etf/ is exactly [date, close] (charter R1 write spec).
      Violations today: BIL EWT GDXJ INDA XLC XLRE are 6-col OHLCV.

  I2  no iShares country-fund carries the dup-frame/truncation signature:
      a fresh-stitched start materially earlier than the on-disk start.
      Violation today: EWA on disk starts 2012-10-12 (3493 rows) while the EW*
      family (EWC/EWM/EWW/EWJ/... all iShares MSCI country funds) starts
      1996-03-18 on disk -> EWA silently lost ~16 years and now masquerades as
      a 2012-inception PASS_WAIVER row.

  I3  post-fix: every EW* country fund on disk starts no later than its
      R2-measured attainable start (results_extend_all.json). 1996-03-18 cohort:
      EWA EWC EWM EWW. Genuine 2000-cohort inceptions (R2 NO_GAIN/EXTENDED at
      these exact dates, matching iShares launch history): EWT 2000-06-23,
      EWY 2000-05-12, EWZ 2000-07-14. A start later than attainable = silent
      truncation -> fail loud.
"""
import os
import pandas as pd
import pytest

OUT = "/Users/daxu/software/world-trader/tools/quant/data/more_etf"
# Per-fund R2-measured attainable starts (results_extend_all.json + NO_GAIN
# rechecks recorded in FINDINGS R2). Later on-disk start = silent truncation.
EW_ATTAINABLE = {
    "EWA": pd.Timestamp("2008-01-02"),   # measured +1206 rows, seam 0.00000
    "EWC": pd.Timestamp("2008-01-02"),   # R2-measured attainable (vendor 1996;
                                         # TwelveData depth begins here)
    "EWM": pd.Timestamp("1996-03-18"),
    "EWW": pd.Timestamp("1996-03-18"),
    "EWT": pd.Timestamp("2000-06-23"),   # NO_GAIN: already at vendor inception
    "EWY": pd.Timestamp("2000-05-12"),
    "EWZ": pd.Timestamp("2000-07-14"),
}


def _csvs():
    return sorted(f for f in os.listdir(OUT)
                  if f.endswith(".csv") and f != "manifest.csv")


def test_all_files_two_columns():
    bad = []
    for f in _csvs():
        cols = list(pd.read_csv(f"{OUT}/{f}", nrows=1).columns)
        if cols != ["date", "close"]:
            bad.append((f, cols))
    assert not bad, f"non-[date,close] files: {bad}"


def test_ew_funds_at_attainable_start():
    bad = []
    for f in _csvs():
        sym = f[:-4]
        if sym not in EW_ATTAINABLE:
            continue
        first = pd.to_datetime(pd.read_csv(f"{OUT}/{f}", nrows=1)["date"].iloc[0])
        if first > EW_ATTAINABLE[sym]:
            bad.append((sym, str(first.date()), str(EW_ATTAINABLE[sym].date())))
    assert not bad, f"EW* funds truncated vs attainable start: {bad}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
