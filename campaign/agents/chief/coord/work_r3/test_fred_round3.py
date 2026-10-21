"""TDD for DATA_FREDMORE round-3 (charter 2026-09-07 07:2x).

(a) ALFRED first-release vintages -> tools/quant/data/alfred/<series>/vintage.csv
    columns [release_date, observation_date, value]; fail-closed lint
    release_date >= observation_date + known_publication_lag(series);
    series with no vintage metadata dropped LOUDLY.
(b) reconcile the 7 pre-R1 lint-FAIL files: alternate-series backfill attempt each;
    where the FAIL was a linter artifact, fix the LINTER under TDD (not the data):
      - MORTGAGE30US: weekly grid ignores holiday-shifted publication (max spacing 9d
        proves no missing week) -> holiday-tolerant weekly lint, default strict.
      - GFDEGDQ188S: quarterly native mis-linted as monthly (241/241 quarterly slots
        present) -> quarterly frequency support in detect_freq/lint.
      - TEDRATE stays FAIL (lint is law): max_run=3 is 5 Christmas closure clusters
        (1993/1999/2004/2010/2021-12-24..28); R2's reason string @1986-01-20 was wrong.
No splices, no deletion. Run: pytest test_fred_round3.py -q
"""
import sys, os, csv, datetime as dt
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/alfred")
import fred_dl

try:
    import alfred_dl
except ImportError:
    alfred_dl = None

ROOT = "/Users/daxu/software/world-trader"
MFRED = f"{ROOT}/tools/quant/data/more_fred"
ALFRED = f"{ROOT}/tools/quant/data/alfred"

# (series, known_publication_lag floor in days from observation_date, source doc)
LAG_FLOOR = {
    "PAYEMS":   27,  # BLS Employment Situation: first Friday of following month
    "UNRATE":   27,  # same release as PAYEMS
    "CPIAUCSL": 35,  # BLS CPI: mid-following-month (>=35d from month start)
    "ICSA":     4,   # DOL Thu release (5d), Wed before Thanksgiving (4d)
    "RSXFS":    37,  # Census advance retail sales: mid-following-month
    "IPMAN":    41,  # Fed G.14 industrial production: ~17th of following month
}
VINTAGE_SERIES = ["PAYEMS", "UNRATE", "CPIAUCSL", "ICSA", "RSXFS", "IPMAN"]


def read_vintage(sid):
    p = os.path.join(ALFRED, sid, "vintage.csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        r = list(csv.reader(f))
    assert r[0] == ["release_date", "observation_date", "value"], f"{sid} bad header {r[0]}"
    return r[1:]


# ---------- pure-function tests (no network) ----------

def test_alfred_module_exists():
    assert alfred_dl is not None, "tools/quant/data/alfred/alfred_dl.py missing"

def test_parse_ot4_first_release_rows():
    # ot4 row = value-in-effect block; parser must emit (release=realtime_start, obs=date, value)
    blocks = [
        {"realtime_start": "2020-04-03", "realtime_end": "2020-05-07", "date": "2020-03-01", "value": "151786"},
        {"realtime_start": "2020-05-08", "realtime_end": "9999-12-31", "date": "2020-04-01", "value": "."},
    ]
    rows, n_missing = alfred_dl.parse_ot4(blocks)
    assert rows == [("2020-04-03", "2020-03-01", 151786.0)]
    assert n_missing == 1

def test_vintage_lint_fail_closed_on_early_release():
    # release BEFORE obs+floor must FAIL (synthetic): payrolls cannot exist on day 3
    rows = [("2020-03-04", "2020-03-01", 151786.0), ("2020-05-08", "2020-04-01", 151000.0)]
    lr = alfred_dl.lint_vintage(rows, lag_floor=27)
    assert lr["pass"] is False and "early-release" in lr["reason"], lr

def test_vintage_lint_pass_on_realistic_rows():
    rows = [("2020-04-03", "2020-03-01", 151786.0), ("2020-05-08", "2020-04-01", 151000.0)]
    lr = alfred_dl.lint_vintage(rows, lag_floor=27)
    assert lr["pass"] is True and lr["n"] == 2, lr

def test_quarterly_freq_supported():
    # GFDEGDQ188S grid: quarterly first-of-month Jan/Apr/Jul/Oct (21 rows = 5.25y)
    rows, y, m = [], 2006, 1
    for i in range(21):
        rows.append((dt.date(y, m, 1).isoformat(), float(i)))
        m += 3
        if m > 12:
            y, m = y + 1, m - 12
    assert fred_dl.detect_freq(rows) == "quarterly", fred_dl.detect_freq(rows)
    lr = fred_dl.lint(rows, freq="quarterly")
    assert lr["pass"] is True and lr["gaps"] == 0, lr

def test_quarterly_lint_still_fails_on_missing_quarter():
    rows = [("2010-01-01", 1.0), ("2010-04-01", 2.0), ("2010-10-01", 4.0)]  # 2010-07-01 missing
    lr = fred_dl.lint(rows, freq="quarterly")
    assert lr["pass"] is False and lr["gaps"] == 1, lr

def test_weekly_holiday_tolerant_lint_mortgage_passes():
    # on-disk MORTGAGE30US: publication shifted +-1..4d around Thurs holidays; max spacing 9d
    p = os.path.join(MFRED, "MORTGAGE30US.csv")
    with open(p) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    strict = fred_dl.lint(rows, freq="weekly")
    tol = fred_dl.lint(rows, freq="weekly", holiday_tol_days=3)
    assert strict["pass"] is False, "strict weekly must keep failing (1194 grid slots)"
    assert tol["pass"] is True and tol["gaps"] == 0, tol

def test_weekly_holiday_tol_negative_control_real_hole_still_fails():
    # two weeks 7d apart, then next obs 21d later: a genuinely missing 2 weeks -> FAIL
    rows = [("2020-01-02", 1.0), ("2020-01-09", 2.0), ("2020-01-30", 3.0)]
    lr = fred_dl.lint(rows, freq="weekly", holiday_tol_days=3)
    assert lr["pass"] is False, lr

# ---------- data-backed tests (fetcher must have run) ----------

@pytest.mark.parametrize("sid", VINTAGE_SERIES)
def test_vintage_file_present_valid(sid):
    rows = read_vintage(sid)
    assert rows is not None, f"{ALFRED}/{sid}/vintage.csv missing"
    assert len(rows) >= 200, f"{sid} n={len(rows)} < 200 (span gate)"
    rel = [dt.date.fromisoformat(r[0]) for r in rows]
    obs = [dt.date.fromisoformat(r[1]) for r in rows]
    assert all(rel[i] <= rel[i + 1] for i in range(len(rel) - 1)), f"{sid} release order"
    # fail-closed: release >= obs + lag floor for EVERY row
    early = [(r[0], r[1]) for r in rows
             if (dt.date.fromisoformat(r[0]) - dt.date.fromisoformat(r[1])).days < LAG_FLOOR[sid]]
    assert not early, f"{sid} early releases: {early[:3]}"

def test_vintage_pit_sanity_2020():
    # first prints verified against the historical release record
    pay = {r[1]: r for r in read_vintage("PAYEMS")}
    assert pay["2020-03-01"] == ["2020-04-03", "2020-03-01", "151786"], pay["2020-03-01"]
    un = {r[1]: r for r in read_vintage("UNRATE")}
    assert un["2020-04-01"] == ["2020-05-08", "2020-04-01", "14.7"], un["2020-04-01"]
    ics = {r[1]: r for r in read_vintage("ICSA")}
    assert ics["2020-03-21"] == ["2020-03-26", "2020-03-21", "3283000"], ics["2020-03-21"]

def test_vintage_cpi_missing_first_print_counted():
    # Oct-2025 CPI: BLS never published; ot4 carries '.' -> dropped, counted, release known
    rows = read_vintage("CPIAUCSL")
    assert all(r[2] != "." for r in rows)
    man = _manifest()
    assert man["ALFRED:CPIAUCSL"]["missing_codes"] == "1", man["ALFRED:CPIAUCSL"]

def test_no_vintage_series_dropped_loudly():
    # SP500 has no ALFRED vintages: must be recorded FAIL, no file written
    assert not os.path.exists(os.path.join(ALFRED, "SP500", "vintage.csv"))
    man = _manifest()
    assert "ALFRED:SP500" in man, "loud drop not recorded"
    assert man["ALFRED:SP500"]["lint_pass"] == "False"
    assert "no-vintages" in man["ALFRED:SP500"]["reason"], man["ALFRED:SP500"]["reason"]

def test_manifest_rows_extended_vintage_lag_days():
    man = _manifest()
    for sid in VINTAGE_SERIES:
        row = man[f"ALFRED:{sid}"]
        assert row["vintage"] == "True", row
        assert int(row["lag_days"]) == LAG_FLOOR[sid], row

# ---------- (b) reconciliation of the 7 pre-R1 lint-FAIL files ----------

FAIL7 = ["CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS", "TEDRATE", "MORTGAGE30US", "GFDEGDQ188S"]

def _manifest():
    with open(os.path.join(MFRED, "manifest.csv")) as f:
        return {r["series_id"]: r for r in csv.DictReader(f)}

def test_no_files_deleted():
    for sid in FAIL7:
        assert os.path.exists(os.path.join(MFRED, sid + ".csv")), f"{sid} deleted"

def test_reconcile_rows_present_and_honest():
    man = _manifest()
    for sid in FAIL7:
        row = man.get(sid)
        assert row is not None, f"{sid} missing from manifest"
        assert row["reconciled_r3"] == "True", f"{sid} not reconciled"
        assert len(row["reason"]) > 30, f"{sid} reason too thin: {row['reason']}"

def test_mortgage30us_gfdeg_reclassified_pass():
    man = _manifest()
    assert man["MORTGAGE30US"]["lint_pass"] == "True"
    assert "holiday-shifted-publication" in man["MORTGAGE30US"]["reason"]
    assert man["GFDEGDQ188S"]["lint_pass"] == "True"
    assert man["GFDEGDQ188S"]["freq"] == "quarterly"

def test_tedrate_stays_fail_with_corrected_reason():
    # R2 claimed contiguous-hole=3@1986-01-20; reality: 1986-01-20 is a 1-day holiday run,
    # the max-run=3 events are the Christmas closure clusters. Lint stays law: FAIL.
    man = _manifest()
    row = man["TEDRATE"]
    assert row["lint_pass"] == "False"
    assert "1993-12-24..26" in row["reason"] and "2021-12-24..26" in row["reason"], row["reason"]

def test_bls_hole_backfill_attempts_recorded():
    man = _manifest()
    for sid in ["CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS"]:
        assert "backfill=impossible" in man[sid]["reason"], man[sid]["reason"]
    # RRSFS specifically: nominal siblings HAVE Oct-2025 but real series needs missing CPI
    assert "deflator" in man["RRSFS"]["reason"].lower()


# ---------- round-3 write-layer integrity (red 2026-09-07: fetcher crashed mid-write) ----------
#
# Failure being encoded: reconcile_manifest() adds 'reconciled_r3' to 7 rows then writes with
# fieldnames from row 0 (AAA) -> csv.ValidationError mid-write, manifest left truncated.
# Same class: vintage rows (15 fields) were APPENDED under the 13-col header, and the
# missing_first_prints patch re-wrote with fieldnames from row 0 again.

def _manifest_raw_rows():
    with open(os.path.join(MFRED, "manifest.csv")) as f:
        return list(csv.DictReader(f))

def _manifest_header():
    with open(os.path.join(MFRED, "manifest.csv")) as f:
        return next(csv.reader(f))

def test_manifest_header_covers_all_row_keys():
    rows = _manifest_raw_rows()
    hdr = set(_manifest_header())
    strays = set()
    for r in rows:
        strays |= set(r) - hdr
    assert not strays, f"row keys not in header: {sorted(strays)} (truncated/corrupt write)"

def test_manifest_no_duplicate_series_rows():
    rows = _manifest_raw_rows()
    ids = [r["series_id"] for r in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate manifest rows (append path not idempotent): {dupes}"

def test_vintage_file_paths_resolve():
    man = _manifest()
    for sid in VINTAGE_SERIES:
        p = man[f"ALFRED:{sid}"]["file"]
        assert p and os.path.exists(os.path.join(ROOT, p)), \
            f"{sid} file path '{p}' does not resolve from repo root"

def test_no_false_novintages_claims():
    # live vintagedates 2026-09-07: VIXCLS/DGS10/DEXJPUS DO have ALFRED vintages
    # (n=3927/5103/651) -> a 'no-vintages' FAIL row for them is a false claim.
    man = _manifest()
    for sid in ["VIXCLS", "DGS10", "DEXJPUS"]:
        row = man.get(f"ALFRED:{sid}")
        assert row is None or "no-vintages" not in row["reason"], \
            f"{sid}: manifest claims no-vintages but series HAS ALFRED vintages"
    assert man["ALFRED:SP500"]["lint_pass"] == "False"  # the one genuine loud drop


def test_fetch_first_release_unpack_contract():
    # regression: fetcher must unpack the (payload, n_missing), err contract;
    # wrong unpack killed the first R3 run before any file was written
    import inspect
    src = inspect.getsource(alfred_dl.fetch_first_release)
    assert "return parse_ot4" in src, "alfred_dl must return (parse_ot4(...), err) form"
    # and the fetcher uses the nested form
    fsrc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "fetch_round3.py")).read()
    assert "(payload, n_missing), err = alfred_dl.fetch_first_release" in fsrc, \
        "fetcher must unpack nested (rows,n_missing),err tuple"


# ---------- round-3 honesty fix (found in independent verification 2026-09-07) ----------
# fetch_round3.py's TEDRATE reason asserted "1986-01-20 has data". grep of TEDRATE.csv
# proves 1986-01-20 is ABSENT (MLK Day, first federal observance 1986): isolated 1-day
# holiday gap, lint-OK, but the reason string claimed the datum exists = false claim
# (O5.7 statistical-truthfulness). Test encodes the real fact; reason string corrected.

def test_tedrate_1986mlk_absent_but_isolated_1day_gap():
    import datetime as _dt
    with open(os.path.join(MFRED, "TEDRATE.csv")) as f:
        ds = [r[0] for r in list(csv.reader(f))[1:]]
    have = set(ds)
    assert "1986-01-20" not in have, "precondition: 1986-01-20 absent from TEDRATE.csv"
    # neighbors 1986-01-17 (Fri) and 1986-01-21 (Tue) present -> exactly 1 missing bday
    assert "1986-01-17" in have and "1986-01-21" in have
    # and it is NOT part of any >=2-bday missing run (bday-aware: weekends don't split)
    a, b = _dt.date.fromisoformat(ds[0]), _dt.date.fromisoformat(ds[-1])
    runs, cur = [], None
    d = a
    while d <= b:
        if d.weekday() < 5 and d.isoformat() not in have:
            cur = d if cur is None else cur
        elif d.weekday() < 5:
            if cur is not None:
                runs.append((cur, d - _dt.timedelta(days=1)))
            cur = None
        d += _dt.timedelta(days=1)
    touching = [r for r in runs if r[0] <= _dt.date(1986, 1, 20) <= r[1]]
    assert touching == [( _dt.date(1986, 1, 20), _dt.date(1986, 1, 20))], touching
    # run length in MISSING BDAY terms, not calendar days (1993-12-24..28 = 5 calendar
    # days but 3 missing bdays; the linter counts bdays and is the authority).
    def n_bdays(r):
        n, d = 0, r[0]
        while d <= r[1]:
            if d.weekday() < 5:
                n += 1
            d += _dt.timedelta(days=1)
        return n
    assert all(n_bdays(r) <= 3 for r in runs), "max missing-bday run must stay 3"
    xmas3 = sorted(r[0].year for r in runs if n_bdays(r) == 3)
    assert xmas3 == [1993, 1999, 2004, 2010, 2021], xmas3

def test_tedrate_reason_no_false_has_data_claim():
    man = _manifest()
    reason = man["TEDRATE"]["reason"]
    assert "1986-01-20 has data" not in reason, reason
    assert "1986-01-20 absent" in reason and "MLK" in reason, reason

def test_pass_rows_have_files_r2_invariant_carried():
    # carried from the broken coord/test_fred_round3.py stub (replaced 2026-09-07):
    # ANY manifest row claiming lint_pass=True must point at an existing file.
    # Path bases in this manifest: bare name -> more_fred/, tools/... or /abs -> as-is.
    for r in _manifest_raw_rows():
        if r["lint_pass"] != "True":
            continue
        f = r.get("file", "")
        assert f, f"{r['series_id']} claims lint_pass=True with no file"
        cands = [os.path.join(MFRED, f), os.path.join(ROOT, f), f]
        assert any(os.path.exists(c) for c in cands), \
            f"{r['series_id']} file missing: {f}"
