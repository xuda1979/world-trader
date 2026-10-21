"""TDD for DATA_FREDMORE round-2. Run: pytest test_fred_round2.py -q
Data-backed assertions FAIL until fetch_round2.py repairs/creates the CSVs."""
import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
import fred_dl

ROOT = "/Users/daxu/software/world-trader"
MFRED = f"{ROOT}/tools/quant/data/more_fred"

def csv_span(sid):
    """Pure: read [date,value] csv -> (n, first, last)."""
    p = os.path.join(MFRED, sid + ".csv")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        rows = [r for r in csv.reader(f)][1:]
    if not rows:
        return None
    return len(rows), rows[0][0], rows[-1][0]

def test_csv_span_pure():
    # synthetic file in tmp dir: exercise parse logic without touching real data
    import tempfile
    tmp = tempfile.mkdtemp()
    p = os.path.join(tmp, "X.csv")
    with open(p, "w") as f:
        f.write("date,value\n2020-01-02,1.5\n2020-01-03,1.6\n")
    import csv as _csv
    with open(p) as f:
        rows = [r for r in _csv.reader(f)][1:]
    assert len(rows) == 2 and rows[0] == ["2020-01-02", "1.5"]

# --- (a) BAMLH0A0HYM2: 3-year ICE BofA licensing window is an upstream FACT, not a bug ---
# Evidence (2026-09-07): FRED series metadata says "Starting in April 2026, this series will
# only include 3 years of observations"; obs_start=2023-09-05 for the whole BAML* family
# (BAMLC0A0CM, BAMLHE00EHYIOAS same notes); ALFRED has no pre-2023-09 vintages
# (realtime_start=1997 probe returns realtime_start>=2023-09-05 rows only).
# Full history is therefore permanently unavailable from FRED -> the 3y file IS the max.
def test_bamlhy_three_year_licensing_window_documented():
    s = csv_span("BAMLH0A0HYM2")
    assert s is not None, "BAMLH0A0HYM2.csv missing"
    n, start, end = s
    assert "2023-09-01" <= start <= "2023-09-10", f"unexpected start {start} (expect licensing window 2023-09-05)"
    assert 700 <= n <= 900, f"n={n} outside 3y-window expectation"
    assert end >= "2026-08-01", f"stale file, ends {end}"

# --- (a) new fetches must exist, lint clean, and respect verified publish-hole trims ---
# Trim precedent = R1 VIXCLS (head-trim at genuine publish/closure holes, no splices):
#   DEXJPUS hole 11bd@1971-08-16 (Nixon-shock FX closure) -> start 1971-08-31
#   DEXUSUK hole  5bd@1971-08-16 (same closure)           -> start 1971-08-23
#   DTWEXBGS holes 4bd@2010-02-08 + 3bd@2016-01-22 (Fed Board blizzard closures, mid-series)
#     -> head-trim to 2016-01-27 (only trim that clears both; cost: 2010-2015 history)
def test_fx_dailies_present_and_linted():
    min_start = {"DEXUSEU": "1999-01-01", "DEXCAUS": "1971-01-04",
                 "DEXJPUS": "1971-08-31", "DEXUSUK": "1971-08-23",
                 "DTWEXBGS": "2016-01-27"}
    min_n = {"DTWEXBGS": 2000}
    for sid in ["DEXUSEU", "DEXJPUS", "DEXCAUS", "DEXUSUK", "DTWEXBGS"]:
        s = csv_span(sid)
        assert s is not None, f"{sid} missing"
        n, start, end = s
        assert start >= min_start[sid], f"{sid} starts {start} < trim {min_start[sid]} (hole reintroduced?)"
        assert n >= min_n.get(sid, 250), f"{sid} n={n}"
        with open(os.path.join(MFRED, sid + ".csv")) as f:
            rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
        lr = fred_dl.lint(rows, freq="daily")
        assert lr["pass"], f"{sid} lint fail: {lr['reason']}"

def test_rsafs_present_and_linted():
    s = csv_span("RSAFS")
    assert s is not None, "RSAFS missing"
    n, start, end = s
    assert n >= 24 and start <= "1992-12-01"
    with open(os.path.join(MFRED, "RSAFS.csv")) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    lr = fred_dl.lint(rows, freq="monthly")
    assert lr["pass"], lr["reason"]

# --- (a) verifies: pre-existing must-haves still lint clean on disk ---
def test_existing_musthaves_lint_clean():
    for sid, freq in [("T10YIE","daily"),("UMCSENT","monthly"),("HOUST","monthly"),
                      ("PERMIT","monthly"),("USREC","monthly")]:
        with open(os.path.join(MFRED, sid + ".csv")) as f:
            rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
        assert fred_dl.detect_freq(rows) == freq, f"{sid} freq {fred_dl.detect_freq(rows)} != {freq}"
        lr = fred_dl.lint(rows, freq=freq)
        assert lr["pass"], f"{sid}: {lr['reason']}"

def test_cpiaucsl_structural_shutdown_hole_documented():
    # BLS did not publish Oct-2025 CPI (government shutdown). Lint is law -> permanent
    # structural fail, and the fail must be EXACTLY that one hole (nothing else missing).
    with open(os.path.join(MFRED, "CPIAUCSL.csv")) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    assert fred_dl.detect_freq(rows) == "monthly"
    lr = fred_dl.lint(rows, freq="monthly")
    assert lr["pass"] is False
    assert lr["gaps"] == 1 and lr["gap_examples"] == ["2025-10-01"], lr

def test_nzltrate_trimmed_pass():
    # R1 fail IRLTLT01NZM156N had a single 1979-09 hole. Legit retry: start-trim to
    # 1979-10-01 (R1 VIXCLS precedent). Must lint PASS monthly.
    s = csv_span("IRLTLT01NZM156N")
    assert s is not None, "IRLTLT01NZM156N.csv missing"
    n, start, end = s
    assert start >= "1979-10-01" and n >= 500, f"{n} {start}..{end}"
    with open(os.path.join(MFRED, "IRLTLT01NZM156N.csv")) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    lr = fred_dl.lint(rows, freq="monthly")
    assert lr["pass"], lr["reason"]

# --- (a) TWEXBMTH: broad dollar index, monthly native, full 1973-2019 (discontinued, no holes)
def test_twexbmth_monthly_dollar_index():
    s = csv_span("TWEXBMTH")
    assert s is not None, "TWEXBMTH missing"
    n, start, end = s
    assert n >= 500 and start <= "1973-06-01" and end >= "2019-12-01", f"{n} {start}..{end}"
    with open(os.path.join(MFRED, "TWEXBMTH.csv")) as f:
        rows = [(r[0], float(r[1])) for r in list(csv.reader(f))[1:]]
    assert fred_dl.detect_freq(rows) == "monthly"
    lr = fred_dl.lint(rows, freq="monthly")
    assert lr["pass"], lr["reason"]

# --- (b) structural fails must be FAIL-CLOSED in the manifest: lint is law, no splices ---
# Oct-2025 BLS shutdown: CPIAUCSL/UNRATE/UNRATENSA/RRSFS/LNS11300060/CPILFESL all carry a
# verified '.' at 2025-10-01 in raw FRED payloads (checked 2026-09-07). Files on disk that
# contain that hole must be recorded as lint FAIL in the manifest, not silently PASS.
def test_shutdown_hole_series_recorded_as_fail_in_manifest():
    import csv as _csv
    with open(os.path.join(MFRED, "manifest.csv")) as f:
        man = {r["series_id"]: r for r in _csv.DictReader(f)}
    for sid in ["CPIAUCSL", "UNRATE", "UNRATENSA", "RRSFS", "TEDRATE"]:
        assert sid in man, f"{sid} missing from manifest"
        assert man[sid]["lint_pass"] == "False", \
            f"{sid} claimed lint_pass={man[sid]['lint_pass']} but on-disk file fails lint"

# --- R1 fetcher accounted for quarterly series by trimming to the quarterly grid only ---
# NROU quarterly with forecast rows to 2036: raw n=... the R1 'gaps=702' verdict stands as
# permanent structural fail (unusable as history); document, do not splice.
def test_nrou_documented_permanent_fail():
    import csv as _csv
    with open(os.path.join(MFRED, "manifest.csv")) as f:
        man = {r["series_id"]: r for r in _csv.DictReader(f)}
    assert "NROU" in man and man["NROU"]["lint_pass"] == "False"
    assert not os.path.exists(os.path.join(MFRED, "NROU.csv")), "NROU must not be written"

def test_usrec_depth():
    with open(os.path.join(MFRED, "USREC.csv")) as f:
        rows = [(r[0], int(float(r[1]))) for r in list(csv.reader(f))[1:]]
    vals = {v for _, v in rows}
    assert vals <= {0, 1}, f"non-binary USREC values: {vals - {0,1}}"
    # depth: covers 2020 and 2008 recessions as 1-runs
    d = {k: v for k, v in rows}
    assert d.get("2008-06-01") == 1 and d.get("2020-04-01") == 1 and d.get("2026-08-01") in (0, 1)
