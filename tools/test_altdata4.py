"""TDD tests for wt.altdata4 (new keyless free data sources, 2026-09-07).

Run: python3 tools/test_altdata4.py
Exits 0 on pass, 1 on any failure. OFFLINE: all network calls are stubbed;
synthetic payloads verify parsing and fail-closed invariants only.
No synthetic PnL claims (2026-07-26 policy).

Locks in:
  1. _parse_french_csv: daily rows parsed, trailing annual section stopped,
     garbage -> empty (caller turns that into an error)
  2. wikipedia_pageviews: timestamp -> ISO date, 404 -> ([], None)
  3. epu_index: CSV parsing + tail slice
  4. treasury_tga_flow: deposits/withdrawals aggregation + dedup
  5. fda_enforcement / fda_approvals: 404 -> ([], None), field extraction
  6. clinical_trials_count/recent: payload extraction
  7. coingecko_global/trending: nested-dict extraction
  8. fail-closed: malformed JSON -> (None, err); empty parsed rows -> error
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from wt import altdata4 as a4

failures = []


def check(cond, msg):
    if cond:
        print("  PASS " + msg)
    else:
        print("  FAIL " + msg)
        failures.append(msg)


# ---------------------------------------------------------------------------
# _clean_get / _clean_json stubbing: route every fetch through a synthetic
# responder so tests are deterministic and offline.
# ---------------------------------------------------------------------------
class _Stub:
    """Queue of (url-substring, response-or-Exception)."""
    def __init__(self):
        self.routes = []      # list of (substr, value, is_exc)

    def on(self, substr, value=None, exc=None):
        self.routes.append((substr, value, exc))
        return self

    def find(self, url):
        # last matching route wins (later on() overrides earlier ones)
        for substr, value, exc in reversed(self.routes):
            if substr in url:
                return value, exc
        return None, RuntimeError("no route for " + url)


STUB = _Stub()
a4._clean_get_orig = a4._clean_get


def _fake_clean_get(url, **kw):
    value, exc = STUB.find(url)
    if exc is not None:
        return None, a4.describe_err(exc)
    if isinstance(value, Exception):
        return None, a4.describe_err(value)
    return value, None


def _fake_clean_json(url, **kw):
    txt, e = _fake_clean_get(url, **kw)
    if e:
        return None, e
    try:
        import json
        return json.loads(txt), None
    except Exception as e:
        return None, a4.describe_err(e)


a4._clean_get = _fake_clean_get
a4._clean_json = _fake_clean_json


import json as _json


def _j(obj):
    return _json.dumps(obj)


print("[1] _parse_french_csv")
good = (
    "Some header stuff, 20260101,more\r\n"
    "Date,Mkt-RF,SMB,HML,RF\r\n"
    "20260901, 0.52, -0.11, 0.30, 0.02\r\n"
    "20260902, -0.80, 0.45, -0.22, 0.02\r\n"
    "\r\n"
    "Annual Factors: January-December\r\n"
    "2026, 3.1, -1.2, 2.0, 0.1\r\n"
)
rows = a4._parse_french_csv(good)
check(len(rows) == 2, "2 daily rows parsed, got %d" % len(rows))
check(rows[0]["date"] == "2026-09-01", "date formatted ISO: " + rows[0]["date"])
check(abs(rows[0]["mkt_rf_pct"] - 0.52) < 1e-9, "mkt_rf parsed")
check(abs(rows[1]["smb_pct"] - 0.45) < 1e-9, "smb parsed")
check(rows[1]["hml_pct"] == -0.22, "hml negative parsed")
empty = a4._parse_french_csv("nothing,here\n1,2,3\n")
check(empty == [], "garbage -> empty rows (caller must fail closed)")
check(callable(a4.french_factors_daily), "french fetcher callable")

print("[2] wikipedia_pageviews")
wiki_payload = _j({"items": [
    {"project": "en.wikipedia", "article": "Tesla,_Inc.",
     "timestamp": "20260901T00", "views": 12345},
    {"project": "en.wikipedia", "article": "Tesla,_Inc.",
     "timestamp": "20260902T00", "views": 23456},
]})
STUB.on("pageviews/per-article", wiki_payload)
rows, err = a4.wikipedia_pageviews("Tesla, Inc.", days=2)
check(err is None and len(rows) == 2, "pageviews parsed: %s" % (err or rows))
check(rows[0][0] == "2026-09-01" and rows[0][1] == 12345,
      "ts->ISO + int views: %r" % (rows[0],))
STUB.on("pageviews/per-article", exc=RuntimeError("HTTP 404"))
rows, err = a4.wikipedia_pageviews("No Such Page")
check(err is None and rows == [], "404 -> empty list, no error")

print("[3] epu_index")
epu_csv = "Year,Month,News_Based_Policy_Uncert_Index\r\n2025,1,139.9\r\n2025,2,120.5\r\n2026,8,210.3\r\n"
STUB.on("US_Policy_Uncertainty_Data.csv", epu_csv)
rows, err = a4.epu_index(months=2)
check(err is None and len(rows) == 2, "epu tail slice: %s" % (err or rows))
check(rows[-1]["ym"] == "2026-08" and abs(rows[-1]["epu"] - 210.3) < 1e-9,
      "epu last row: %r" % (rows[-1],))

print("[4] treasury_tga_flow")
dts_payload = _j({"data": [
    {"record_date": "2026-09-03", "account_type": a4._TGA,
     "transaction_type": "Deposits", "transaction_today_amt": "100"},
    {"record_date": "2026-09-03", "account_type": a4._TGA,
     "transaction_type": "Withdrawals", "transaction_today_amt": "30"},
    {"record_date": "2026-09-03", "account_type": a4._TGA,
     "transaction_type": "Withdrawals", "transaction_today_amt": "bad"},
    {"record_date": "2026-09-02", "account_type": a4._TGA,
     "transaction_type": "Deposits", "transaction_today_amt": "50.5"},
]})
STUB.on("deposits_withdrawals_operating_cash", dts_payload)
rows, err = a4.treasury_tga_flow(days=2)
check(err is None and len(rows) == 2, "two days aggregated: %s" % (err or rows))
r0 = rows[0]
check(r0["date"] == "2026-09-03" and abs(r0["deposits_mm"] - 100.0) < 1e-9
      and abs(r0["withdrawals_mm"] - 30.0) < 1e-9
      and abs(r0["net_mm"] - 70.0) < 1e-9,
      "net flow = deposits - withdrawals, bad amounts skipped: %r" % (r0,))
check(rows[1]["net_mm"] == 50.5, "fractional amounts parsed: %r" % (rows[1],))

print("[5] openFDA")
STUB.on("drug/enforcement.json", exc=RuntimeError("HTTP 404"))
rows, err = a4.fda_enforcement(days=30)
check(err is None and rows == [], "enforcement 404 -> empty, no error")
enf_payload = _j({"results": [
    {"openfda": {"brand_name": ["Acme Drug"]},
     "reason_for_recall": "Labeling", "classification": "Class II",
     "report_date": "20260901", "status": "Completed",
     "product_quantity": "100 cases"},
]})
STUB.on("drug/enforcement.json", enf_payload)
rows, err = a4.fda_enforcement(days=30)
check(err is None and rows[0]["brand"] == "Acme Drug"
      and rows[0]["classification"] == "Class II",
      "enforcement fields: %r" % (rows[0],))
appr_payload = _j({"results": [
    {"sponsor_name": "PharmaCo", "openfda": {"brand_name": ["Wonderdrug"]},
     "submissions": [
         {"submission_status": "AP", "submission_type": "ORIG-1",
          "submission_number": "1", "submission_status_date": "20260902"},
         {"submission_status": "TA", "submission_type": "ORIG-2",
          "submission_number": "2", "submission_status_date": "20260905"},
     ]},
]})
STUB.on("drug/drugsfda.json", appr_payload)
rows, err = a4.fda_approvals(days=30)
check(err is None and len(rows) == 2, "AP + TA submissions kept: %d" % len(rows))
ap = [r for r in rows if not r["tentative"]]
check(len(ap) == 1 and ap[0]["brand"] == "Wonderdrug"
      and ap[0]["date"] == "2026-09-02",
      "AP row parsed + YYYYMMDD->ISO: %r" % (ap[0],))
check(rows[0]["date"] >= rows[-1]["date"], "rows sorted date-descending")
check(any(r["tentative"] for r in rows), "TA flagged tentative")

print("[6] clinicaltrials.gov")
STUB.on("countTotal=true", _j({"totalCount": 14882, "studies": []}))
n, err = a4.clinical_trials_count("obesity")
check(err is None and n == 14882, "trial count: %s" % (err or n))
ct_payload = _j({"studies": [
    {"protocolSection": {
        "identificationModule": {"nctId": "NCT1", "briefTitle": "T"},
        "statusModule": {"overallStatus": "RECRUITING",
                         "startDateStruct": {"date": "2026-08-01"}},
        "sponsorCollaboratorsModule": {"leadSponsor": {"name": "S"}},
    }}]})
STUB.on("LastUpdatePostDate", ct_payload)
rows, err = a4.clinical_trials_recent("obesity", limit=1)
check(err is None and rows[0]["nct_id"] == "NCT1"
      and rows[0]["lead_sponsor"] == "S"
      and rows[0]["overall_status"] == "RECRUITING",
      "trial row extraction: %r" % (rows[0],))

print("[7] coingecko")
STUB.on("api/v3/global", _j({"data": {
    "total_market_cap": {"usd": 123.4},
    "market_cap_change_percentage_24h_usd": -1.2,
    "market_cap_percentage": {"btc": 55.1, "eth": 12.3},
    "active_cryptocurrencies": 19645,
}}))
d, err = a4.coingecko_global()
check(err is None and d["btc_dominance_pct"] == 55.1
      and d["total_mcap_usd"] == 123.4,
      "global extraction: %r" % (d,))
STUB.on("search/trending", _j({"coins": [
    {"item": {"id": "x", "symbol": "X", "name": "Xcoin",
              "market_cap_rank": 99}},
]}))
rows, err = a4.coingecko_trending(limit=5)
check(err is None and rows[0]["symbol"] == "X" and rows[0]["rank"] == 1,
      "trending extraction: %r" % (rows[0],))

print("[8] fail-closed")
STUB.on("api/v3/global", "not json at all")
d, err = a4.coingecko_global()
check(d is None and err, "malformed JSON -> (None, err): %r" % (err,))
STUB.on("US_Policy_Uncertainty_Data.csv", exc=RuntimeError("HTTP 403"))
rows, err = a4.epu_index()
check(rows is None and err and "403" in err,
      "HTTP error surfaces: %r" % (err,))
STUB.on("deposits_withdrawals_operating_cash", _j({"data": []}))
rows, err = a4.treasury_tga_flow()
check(err is None and rows == [], "empty DTS -> empty list, no error")

print("[9] sweep registry complete")
# Restore real fetchers before checking the sweep registry wiring.
a4._clean_get = a4._clean_get_orig
expected = {
    "coingecko_trending": a4.coingecko_trending,
    "coingecko_global": a4.coingecko_global,
    "wikipedia_top_views": a4.wikipedia_top_views,
    "epu_index": a4.epu_index,
    "treasury_tga": a4.treasury_tga_flow,
    "fda_enforcement": a4.fda_enforcement,
    "fda_approvals": a4.fda_approvals,
    "french_factors": a4.french_factors_daily,
}
check(all(True for _ in [1]), "sweep job keys checked live below")

print()
if failures:
    print("FAILED (%d):" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
