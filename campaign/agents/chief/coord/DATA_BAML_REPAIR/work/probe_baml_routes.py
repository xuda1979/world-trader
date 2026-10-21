#!/usr/bin/env python3
"""DATA_BAML_REPAIR — decisive 3-route probe for BAMLH0A0HYM2 history depth.

Contradiction under test:
  - DATA_COVERAGE item-1 (HUNT_CREDIT2 R1): claims FRED serves full 1996-12+
    history (~7,400 rows); on-disk files are windowed-fetch truncations.
  - HUNT_CREDIT2 R2 FINDINGS: verified the OPPOSITE — every route tried
    (API with observation_start=1996-12-31, fredgraph.csv, aliases) returned
    2023-09+ only (787-796 rows).

Probe routes (all run live, today):
  (a) FRED API, fred_dl.fetch with NO observation_start (repair script's premise:
      "the API returns full native history").
  (b) fredgraph.csv no-key: https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2
  (c) FRED API with explicit observation_start=1996-12-31 (direct urllib, not
      fred_dl, so the parameter construction is independently visible).

Decision rule (pre-registered):
  - FULL history obtainable (any route ~>= 7000 rows starting 1996-12/1997-01)
    -> repair path: run repair_baml_oas.py.
  - ALL routes return 2023-09+ only -> phantom confirmed: DATA_COVERAGE item-1
    corrected as FRED source truncation; R2 verification stands.
  - MIXED -> investigate the route that returned full history before trusting it
    (check for synthetic/backfill markers), then decide.

Fail-closed: prints explicit PASS/FAIL per route; non-zero exit if any route
errors out entirely (network vs. semantic truncation must be distinguishable).
Read-only probe: writes nothing to data directories.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.request

SID = "BAMLH0A0HYM2"
ENV_FILE = "/Users/daxu/software/world-trader/.env.local"
BASE = "https://api.stlouisfed.org/fred/series/observations"
FULL_FLOOR_ROWS = 7000          # ~7,400 expected if 1996-12+ served
FULL_FLOOR_START_YEAR = 1997    # first observation should be Dec-1996/Jan-1997


def get_key():
    key = os.environ.get("FRED_KEY")
    if key:
        return key
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line.startswith("FRED_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("FAIL: no FRED_KEY in env or .env.local")


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "wt-data-probe/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def summarize(rows_dates, label):
    """rows_dates: list of (date_str, value_str) in source order."""
    n = len(rows_dates)
    if n == 0:
        print(f"  [{label}] 0 rows — EMPTY")
        return ("empty", 0, None, None)
    first, last = rows_dates[0][0], rows_dates[-1][0]
    first_year = int(first[:4])
    # decision-relevant classification
    if n >= FULL_FLOOR_ROWS and first_year <= FULL_FLOOR_START_YEAR:
        verdict = "FULL-HISTORY"
    elif first[:7] >= "2023-09":
        verdict = "TRUNCATED-2023-09+"
    else:
        verdict = "PARTIAL"
    print(f"  [{label}] rows={n}  first={first}  last={last}  -> {verdict}")
    return (verdict, n, first, last)


def probe_api_nostart(key):
    """Route (a): fred_dl.fetch(series_id, key) with NO start (repair script premise).
    fred_dl.fetch returns ((rows, n_missing), err) where rows are (date_str, float)."""
    sys.path.insert(0, "/Users/daxu/software/world-trader/tools/quant/data/more_fred")
    import fred_dl
    (rows, n_missing), err = fred_dl.fetch(SID, key)
    if err:
        print(f"  [api-nostart] ERROR: {err}")
        return ("error", 0, None, None)
    dates = [(d, "" if v is None else str(v)) for d, v in rows]
    return summarize(dates, "api-nostart")


def probe_fredgraph():
    """Route (b): fredgraph.csv, no API key."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SID}"
    try:
        text = http_get(url)
    except Exception as e:
        print(f"  [fredgraph] ERROR: {e}")
        return ("error", 0, None, None)
    rdr = csv.reader(io.StringIO(text))
    header = next(rdr, None)
    rows_dates = [(r[0], r[1] if len(r) > 1 else "") for r in rdr if r]
    print(f"  [fredgraph] header={header}")
    return summarize(rows_dates, "fredgraph")


def probe_api_explicit_start(key):
    """Route (c): API with explicit observation_start=1996-12-31, raw urllib."""
    url = (f"{BASE}?series_id={SID}&api_key={key}&file_type=json"
           f"&observation_start=1996-12-31")
    try:
        text = http_get(url)
    except Exception as e:
        print(f"  [api-start-1996] ERROR: {e}")
        return ("error", 0, None, None)
    try:
        js = json.loads(text)
    except Exception as e:
        print(f"  [api-start-1996] ERROR (non-JSON): {e}; first 200 chars: {text[:200]!r}")
        return ("error", 0, None, None)
    if "observations" not in js:
        print(f"  [api-start-1996] ERROR: no 'observations' key; payload keys={list(js)[:8]}; "
              f"first 200: {text[:200]!r}")
        return ("error", 0, None, None)
    obs = js["observations"]
    rows_dates = [(o.get("date", ""), o.get("value", "")) for o in obs]
    return summarize(rows_dates, "api-start-1996")


def main():
    print(f"DATA_BAML_REPAIR probe — {SID} — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    key = get_key()
    print(f"FRED key: loaded (len {len(key)})\n")
    results = {}
    print("Route (a): FRED API, NO observation_start (repair-script premise)")
    results["api_nostart"] = probe_api_nostart(key)
    time.sleep(1.0)
    print("\nRoute (b): fredgraph.csv, no key")
    results["fredgraph"] = probe_fredgraph()
    time.sleep(1.0)
    print("\nRoute (c): FRED API, explicit observation_start=1996-12-31")
    results["api_start_1996"] = probe_api_explicit_start(key)

    print("\n=== VERDICT ===")
    verdicts = {k: v[0] for k, v in results.items()}
    print(f"  {verdicts}")
    any_full = any(v[0] == "FULL-HISTORY" for v in results.values())
    any_error = any(v[0] == "error" for v in results.values())
    if any_error:
        print("  RESULT: INCONCLUSIVE — at least one route errored (network/semantic "
              "truncation must be distinguished before deciding).")
        sys.exit(2)
    if any_full:
        print("  RESULT: FULL HISTORY OBTAINABLE — repair path is live "
              "(inspect the winning route's first rows for backfill markers, then "
              "run repair_baml_oas.py).")
        sys.exit(0)
    print("  RESULT: ALL ROUTES TRUNCATED 2023-09+ (or partial) — phantom confirmed; "
          "DATA_COVERAGE item-1 must be corrected to FRED source truncation; "
          "R2 verification stands.")
    sys.exit(1)


if __name__ == "__main__":
    main()
