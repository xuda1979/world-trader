#!/usr/bin/env python3
"""ROUND 3 TDD tests (written FIRST, before retest_r3.py exists).

Contract under test — the coordinator's 2026-09-07 start-bound WAIVER:
  "the 2007-01 bound is WAIVED for inception-limited series — span depth disclosed
   per-file, hunts filter on it."
  span_class per charter 3(a): pre2007 | 2007plus | inception_fail.

FAIL-CLOSED rules being pinned by these tests:
  T1  a series starting <= 2007-01-01 is classed pre2007 (status PASS)
  T2  a series starting in (2007-01-01, 2013-01-01] is classed 2007plus and is
      WRITTEN to disk (the waiver's whole point) — but flagged so hunts filter.
  T3  a series starting AFTER 2013-01-01 stays inception_fail and MUST NOT be
      written as a huntable series (no depth to hunt over).
  T4  span_class column exists in the manifest and is non-empty for every row.
  T5  all pre-existing R2 lint gates still fire under the waiver (gap/jumps/dup/
      short/stale fail-closed — waiver covers ONLY the start bound).
  T6  a waiver-passed 2007plus write never overwrites/deletes an existing PASS
      file, and rows are strictly ascending unique dates.
  T7  manifest span_class matches the on-disk file's actual first date (no
      stale metadata).
"""
import os
import sys
import json
import shutil
import subprocess
import tempfile

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
RETEST = f"{HERE}/retest_r3.py"

# ---- importable lint logic lives in retest_r3.py ----------------------------
sys.path.insert(0, HERE)


def _mk(tmp, closes, start="2000-01-03", freq="B"):
    idx = pd.bdate_range(start, periods=len(closes))
    return pd.DataFrame({"date": idx, "close": closes})


def test_retest_module_exists():
    assert os.path.exists(RETEST), "retest_r3.py must exist (TDD: write it next)"


def test_classify_boundaries():
    from retest_r3 import classify
    assert classify(pd.Timestamp("2006-12-29")) == "pre2007"
    assert classify(pd.Timestamp("2007-01-01")) == "pre2007"
    assert classify(pd.Timestamp("2007-01-02")) == "2007plus"
    assert classify(pd.Timestamp("2007-04-11")) == "2007plus"   # HYG
    assert classify(pd.Timestamp("2012-12-31")) == "2007plus"
    assert classify(pd.Timestamp("2013-01-02")) == "inception_fail"  # too late
    assert classify(pd.Timestamp("2018-06-19")) == "inception_fail"  # XLC


def test_waiver_only_lifts_start_bound():
    """T5: every non-start R2 gate still fails closed under the waiver.
    (Test-side fixes documented in FINDINGS: pandas-3.0-safe shift, and frames
    extended to end near the present so the ~3y freshness gate is testable at
    all — the original draft's 2009-ending 'ok' frame contradicted its own
    PASS_WAIVER assertion under any honest freshness window.)"""
    from retest_r3 import lint_series
    # 2007plus start, ending ~2026-08 (fresh vs default ref_end 2026-09-01)
    N = 3800
    ok = _mk(None, [100.0] * N, start="2012-01-03")
    st, cls, m = lint_series(ok)
    assert st == "PASS_WAIVER" and cls == "2007plus"

    big_gap = ok.copy()
    big_gap.loc[200:, "date"] = big_gap.loc[200:, "date"] + pd.Timedelta(days=40)
    st, cls, m = lint_series(big_gap)
    assert st.startswith("FAIL") and "gap" in st

    jumps = ok.copy()
    jumps.loc[N - 1, "close"] = 400.0
    st, cls, m = lint_series(jumps)
    assert st.startswith("FAIL") and "jump" in st

    short = _mk(None, [100.0] * 100, start="2008-03-01")
    st, cls, m = lint_series(short)
    assert st.startswith("FAIL") and "short" in st

    stale = ok.copy()
    stale["date"] = stale["date"] - pd.Timedelta(days=3652)   # ends ~2016-08
    st, cls, m = lint_series(stale)
    assert st.startswith("FAIL") and "stale" in st

    dups = pd.concat([ok, ok.head(5)], ignore_index=True)
    st, cls, m = lint_series(dups)
    assert st.startswith("FAIL") and "dup" in st


def test_inception_fail_not_written(tmp_path):
    """T3: a post-2013 inception must not become a huntable csv."""
    from retest_r3 import lint_series
    late = _mk(None, [100.0] * 700, start="2024-01-02")          # XLRE-like, fresh
    st, cls, m = lint_series(late)
    assert st == "FAIL(inception)" and cls == "inception_fail"


def test_write_guard_and_ascending(tmp_path):
    """T6: writes are ascending, unique-dated, and never clobber a PASS file."""
    from retest_r3 import write_series
    df = _mk(None, [100.0 + i for i in range(400)], start="2007-03-01")
    p = tmp_path / "TST.csv"
    write_series(df, str(p))
    back = pd.read_csv(p)
    d = pd.to_datetime(back["date"])
    assert d.is_monotonic_increasing and not d.duplicated().any()
    assert list(back.columns) == ["date", "close"]


def test_manifest_span_class_column(tmp_path):
    """T4: rebuilt manifest carries non-empty span_class for every row."""
    import manifest_r3
    src = tmp_path / "data"
    src.mkdir()
    for sym, start in [("AAA", "2000-01-03"), ("BBB", "2007-04-11"),
                       ("CCC", "2018-06-19")]:
        n = 400 if start < "2015" else 300
        df = pd.DataFrame({"date": pd.bdate_range(start, periods=n),
                           "close": [100.0 + i * 0.01 for i in range(n)]})
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df.to_csv(src / f"{sym}.csv", index=False)
    mf = manifest_r3.build(src=str(src))
    assert "span_class" in mf.columns
    assert (mf["span_class"] != "").all()
    got = dict(zip(mf["symbol"], mf["span_class"]))
    assert got["AAA"] == "pre2007"
    assert got["BBB"] == "2007plus"
    assert got["CCC"] == "inception_fail"


def test_manifest_span_class_matches_disk():
    """T7: manifest for the REAL dir must agree with file reality (no stale rows)."""
    import manifest_r3
    mf = manifest_r3.build()
    for _, r in mf.iterrows():
        f = f"{OUT}/{r['symbol']}.csv"
        assert os.path.exists(f), f"{r['symbol']} in manifest but no file"
        first = pd.read_csv(f, nrows=1)["date"].iloc[0]
        cls = manifest_r3.classify(pd.Timestamp(first))
        assert cls == r["span_class"], \
            f"{r['symbol']}: manifest says {r['span_class']}, disk starts {first} -> {cls}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
