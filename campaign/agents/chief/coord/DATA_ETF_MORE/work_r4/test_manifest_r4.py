"""TDD: after the R4 rotation, manifest.csv must reflect the 5 newly written
files (EIS TUR EPHE COPX ENOR) with span_class + status matching DISK, not
just the R3 77-row state. Failing FIRST (red), then manifest_r4.py."""
import csv

import pandas as pd

D = "/Users/daxu/software/world-trader/tools/quant/data/more_etf"
NEW = ["ENOR", "COPX", "EPHE", "TUR", "EIS"]


def _manifest():
    with open(f"{D}/manifest.csv") as f:
        return {r["symbol"]: r for r in csv.DictReader(f)}


def test_m1_all_78_series_have_manifest_rows():
    files = {fn[:-4] for fn in __import__("os").listdir(D)
             if fn.endswith(".csv") and fn != "manifest.csv"}
    rows = _manifest()
    missing = files - set(rows)
    assert not missing, f"files on disk with NO manifest row: {sorted(missing)}"


def test_m2_new_rows_match_disk():
    rows = _manifest()
    for sym in NEW:
        r = rows.get(sym)
        assert r, f"{sym} missing from manifest"
        df = pd.read_csv(f"{D}/{sym}.csv")
        assert int(r["rows"]) == len(df), sym
        assert r["start"] == df["date"].iloc[0], sym
        assert r["end"] == df["date"].iloc[-1], sym
        assert r["span_class"] == "2007plus", sym
        assert r["status"] == "PASS_WAIVER", sym


def test_m3_independent_relint_of_new_files_is_clean():
    """Fresh logic (not r4_fetch.lint_series): gap<=10, no dups, ascending,
    positive, <=2 days from R3's verified end (2026-09-04)."""
    for sym in NEW:
        df = pd.read_csv(f"{D}/{sym}.csv", parse_dates=["date"])
        s = df.set_index("date")["close"]
        assert s.is_monotonic_increasing or s.index.is_monotonic_increasing, sym
        assert (s > 0).all(), sym
        assert not s.index.duplicated().any(), sym
        gaps = s.index.to_series().diff().dt.days.dropna()
        assert gaps.max() <= 10, f"{sym} maxgap={gaps.max()}"
        assert (s.pct_change().abs() > 0.5).sum() == 0, sym
        assert (pd.Timestamp("2026-09-04") - s.index[-1]).days <= 2, sym
