"""TDD tests for wt.altdata3 POINT-IN-TIME (PIT) fundamentals.

Covers the audit-grade PIT ledger + temporal-rollback snapshot added 2026-09-14:
  - sec_xbrl_series  now carries the SEC `filed` date (the anti-lookahead anchor)
  - sec_pit_ledger   full restatement/amendment trail, filed-sorted
  - sec_pit_snapshot reconstruct a value EXACTLY as it appeared on a given date

Run: python3 tools/test_altdata3_pit.py
Exits 0 on pass, 1 on any failure. OFFLINE: all network calls are stubbed;
synthetic payloads verify parsing + fail-closed invariants only.
Fixtures mirror the real SEC EDGAR companyconcept shape (units -> facts with
start/end/val/form/fp/fy/filed/accn). No synthetic PnL claims (policy 2026-07-26).

Live smoke (optional, network): python3 tools/test_altdata3_pit.py --live
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from wt import altdata3 as a3

failures = []


def check(cond, msg):
    if cond:
        print("  PASS " + msg)
    else:
        print("  FAIL " + msg)
        failures.append(msg)


# ---------------------------------------------------------------------------
# Fixture: a synthetic SEC companyconcept payload with a RESTATEMENT -- the
# same period end re-filed later at a HIGHER value. This is the exact
# lookahead-bias trap PIT is designed to neutralise.
# ---------------------------------------------------------------------------
SEC_PAYLOAD = {
    "entityName": "TEST CORP",
    "ticker": "TEST",
    "units": {
        "USD": [
            # Two distinct annual periods, each filed on its own date.
            {"start": "2019-01-01", "end": "2019-12-31", "val": 1000,
             "form": "10-K", "fp": "FY", "fy": 2019, "filed": "2020-02-15",
             "accn": "0001"},
            {"start": "2020-01-01", "end": "2020-12-31", "val": 2000,
             "form": "10-K", "fp": "FY", "fy": 2020, "filed": "2021-02-14",
             "accn": "0002"},
            # RESTATEMENT: period 2019 re-filed later with a higher value.
            {"start": "2019-01-01", "end": "2019-12-31", "val": 1100,
             "form": "10-K/A", "fp": "FY", "fy": 2019, "filed": "2021-04-01",
             "accn": "0003"},
        ]
    }
}


class _Stub:
    def __init__(self):
        self.routes = []

    def on(self, substr, value=None, exc=None):
        self.routes.append((substr, value, exc))
        return self

    def find(self, url):
        for substr, value, exc in reversed(self.routes):
            if substr in url:
                return value, exc
        return None, RuntimeError("no route for " + url)


STUB = _Stub()
a3._clean_json_orig = a3._clean_json


def _fake_clean_json(url, **kw):
    value, exc = STUB.find(url)
    if exc is not None:
        return None, a3.describe_err(exc)
    if isinstance(value, Exception):
        return None, a3.describe_err(value)
    import json as _json
    return _json.loads(_json.dumps(value)), None


a3._clean_json = _fake_clean_json


# CIK resolution: map ticker -> cik_str in company_tickers.json.
def _cik_payload():
    return {"0": {"cik_str": 1234567890, "ticker": "TEST"}}

STUB.on("company_tickers.json", _cik_payload())
# companyconcept for the CIK + tag.
STUB.on("companyconcept/CIK1234567890/us-gaap/Revenues.json", SEC_PAYLOAD)


print("[1] sec_xbrl_series carries the PIT `filed` timestamp")
rows, err = a3.sec_xbrl_series("TEST", "Revenues", limit=10)
check(err is None, "no fetch error")
check(rows is not None and len(rows) == 3, "all 3 facts returned")
if rows:
    f0 = rows[0]  # sec_xbrl_series sorts by period END desc -> 2020-12-31
    check(f0.get("filed") == "2021-02-14", "top row (2020 period) filed date: %r" % (f0.get("filed"),))
    check(f0.get("end") == "2020-12-31" and f0.get("value") == 2000,
          "top row is the most recent period end (2020-12-31)")
    check(all("filed" in r for r in rows), "every row exposes a `filed` PIT anchor")
    check(any(r.get("form") == "10-K/A" for r in rows), "amendment form surfaced")

print("[2] sec_pit_ledger is filed-sorted and flags amendments")
ledger, err = a3.sec_pit_ledger("TEST", "Revenues")
check(err is None and len(ledger) == 3, "ledger has 3 rows")
if ledger:
    fd = [r["filed"] for r in ledger]
    check(fd == sorted(fd), "ledger sorted by filed date (PIT order): %r" % (fd,))
    amend = [r for r in ledger if r["form"] == "10-K/A"]
    check(len(amend) == 1 and amend[0]["amended"] is True, "10-K/A flagged amended=True")
    normal = [r for r in ledger if r["form"] == "10-K"]
    check(all(r["amended"] is False for r in normal), "plain 10-K flagged amended=False")

print("[3] sec_pit_ledger honors as_of up-front filter (fail-closed)")
ledger_sub, err = a3.sec_pit_ledger("TEST", "Revenues", as_of="2020-03-01")
check(err is None and len(ledger_sub) == 1, "as_of filter keeps only 2019 10-K: %r" % (0 if err else len(ledger_sub),))
if ledger_sub:
    check(ledger_sub[0]["filed"] == "2020-02-15", "kept the fact filed on/before as_of")

print("[4] sec_pit_snapshot temporal rollback (core PIT primitive)")
# Before the 2019 10-K was filed -> NOTHING knowable.
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2020-02-14",
                                   period_end="2019-12-31")
check(err is None and v is None, "as_of before first filing -> value None (no leak)")
# On 2020-02-15 the original 1000 is knowable.
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2020-02-15",
                                   period_end="2019-12-31")
check(err is None and v == 1000 and meta["filed"] == "2020-02-15",
      "as_of on filing date -> original 1000 (filed 2020-02-15)")
# Before the restatement -> still the ORIGINAL 1000 (no lookahead leak).
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2021-03-31",
                                   period_end="2019-12-31")
check(err is None and v == 1000, "before restatement filed -> NOT the revised 1100")
# After the restatement -> the REVISED 1100 is now the true as-of value.
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2021-04-01",
                                   period_end="2019-12-31")
check(err is None and v == 1100 and meta["filed"] == "2021-04-01",
      "after restatement filed -> revised 1100 (rollback applied)")
# Earlier-than-everything -> fail-closed.
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2019-01-01",
                                   period_end="2019-12-31")
check(v is None, "as_of predating all filings -> value None")

print("[6] sec_13f_recent_filings (institutional holdings, PIT-stamped)")
# Submissions payload for a money-manager CIK with 13F-HR entries interleaved
# among many other forms (large-filer realistic shape).
def _submissions_payload():
    return {
        "filings": {"recent": {
            "form": ["8-K", "CERT", "13F-HR", "SC 13G/A", "8-K", "13F-HR/A",
                     "S-8 POS", "424B5"],
            "filingDate": ["2024-01-02", "2024-01-03", "2024-02-13",
                           "2024-02-14", "2024-03-01", "2024-05-10",
                           "2024-05-12", "2024-05-13"],
            "accessionNumber": ["0000000-24-000001", "0000000-24-000002",
                                "0000000-24-000003", "0000000-24-000004",
                                "0000000-24-000005", "0000000-24-000006",
                                "0000000-24-000007", "0000000-24-000008"],
            "primaryDocument": ["a1.htm", "a2.htm", "xslForm13F_X02/primary_doc.xml",
                                "a4.htm", "a5.htm", "xslForm13F_X02/primary_doc.xml",
                                "a7.htm", "a8.htm"],
        }}
    }
STUB.on("submissions/CIK0000001234.json", _submissions_payload())

fils, err = a3.sec_13f_recent_filings(1234, limit=2)
check(err is None, "13F fetch ok")
check(fils is not None and len(fils) == 2,
      "returns the 2 most recent 13F-HR filings: %r" % (0 if err else len(fils),))
if fils:
    # Most recent 13F-HR first (2024-05-10), then 13F-HR/A (2024-02-13).
    check(fils[0]["filing_date"] == "2024-05-10" and fils[0]["form"] == "13F-HR/A",
          "top row is newest 13F (13F-HR/A, filed 2024-05-10), PIT-anchored")
    check(fils[1]["filing_date"] == "2024-02-13" and fils[1]["form"] == "13F-HR",
          "second row is older 13F-HR (filed 2024-02-13)")
    check("filing_date" in fils[0] and "url" in fils[0] and "id" in fils[0],
          "each row PIT-stamped with filing_date + direct holdings URL")
    check(fils[0]["url"].startswith("https://www.sec.gov/Archives/edgar/data/"),
          "URL points into the EDGAR archives (provenance)")
fils_none, err_none = a3.sec_13f_recent_filings(999999999, limit=2)
if err_none is not None or fils_none is None:
    check(True, "CIK with no 13F -> fail-closed (None, err)")
else:
    check(False, "CIK with no 13F should fail closed")

print("[7] field errors fail closed")
STUB3 = _Stub()
STUB3.on("company_tickers.json", _cik_payload())
STUB3.on("companyconcept/CIK1234567890/us-gaap/Revenues.json",
         exc=RuntimeError("dial timeout"))
def _fake_err_json(url, **kw):
    value, exc = STUB3.find(url)
    if exc is not None:
        return None, a3.describe_err(exc)
    return value, None
a3._clean_json = _fake_err_json
rows, err = a3.sec_xbrl_series("TEST", "Revenues")
check(rows is None and err is not None, "network failure on xbrl -> (None, err)")
v, meta, err = a3.sec_pit_snapshot("TEST", "Revenues", as_of="2021-01-01")
check(err is not None, "snapshot propagates fetch error")
a3._clean_json = a3._clean_json_orig  # restore

# ---- OPTIONAL LIVE SMOKE ----
if "--live" in sys.argv:
    print("[LIVE] sec_pit_snapshot vs real SEC EDGAR (requires network)")
    v, meta, err = a3.sec_pit_snapshot("MSFT", "Revenues", as_of="2010-01-27",
                                       period_end="2009-12-31")
    check(err is None and v == 12920000000,
          "MSFT rollback before 2010-01-28 filing: %r (filed %s)" % (v, meta.get("filed") if meta else None))
    v2, meta2, err = a3.sec_pit_snapshot("MSFT", "Revenues", as_of="2010-01-28",
                                         period_end="2009-12-31")
    check(err is None and v2 == 19022000000,
          "MSFT rollback on 2010-01-28 filing: %r (filed %s)" % (v2, meta2.get("filed") if meta2 else None))

if failures:
    print("\n%d FAILURE(S)" % len(failures))
    sys.exit(1)
print("\nALL PIT TESTS PASSED")
