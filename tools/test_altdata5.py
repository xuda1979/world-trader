"""TDD tests for wt.altdata5 (new keyless free data sources, 2026-09-08).

Run: python3 tools/test_altdata5.py
Exits 0 on pass, 1 on any failure. OFFLINE: all network calls are stubbed;
synthetic payloads verify parsing and fail-closed invariants only.
No synthetic PnL claims (2026-07-26 policy).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from wt import altdata5 as a5

failures = []


def check(cond, msg):
    if cond:
        print("  PASS " + msg)
    else:
        print("  FAIL " + msg)
        failures.append(msg)


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
a5._clean_get_orig = a5._clean_get


def _fake_clean_get(url, **kw):
    value, exc = STUB.find(url)
    if exc is not None:
        return None, a5.describe_err(exc)
    if isinstance(value, Exception):
        return None, a5.describe_err(value)
    return value, None


def _fake_clean_json(url, **kw):
    txt, e = _fake_clean_get(url, **kw)
    if e:
        return None, e
    try:
        import json
        return json.loads(txt), None
    except Exception as e:
        return None, a5.describe_err(e)


a5._clean_get = _fake_clean_get
a5._clean_json = _fake_clean_json

import json as _json


def _j(obj):
    return _json.dumps(obj)

print("[1] _f numeric coercion")
check(a5._f("4.625000") == 4.625, "string float parsed")
check(a5._f("") is None, "empty string -> None")
check(a5._f(None) is None, "None -> None")
check(a5._f("n/a") is None, "junk -> None")
check(a5._f(12) == 12.0, "int passthrough")

print("[2] _parse_frank_rates (Frankfurter/ECB FX)")
frank = dict(amount=1.0, base="USD",
             start_date="2026-09-01", end_date="2026-09-02",
             rates=dict([("2026-09-02", dict(CNY=6.71, EUR=0.857)),
                         ("2026-09-01", dict(CNY=6.72, EUR=0.858))]))
rows, err = a5._parse_frank_rates(frank, "CNY")
check(err is None and rows == [("2026-09-01", 6.72), ("2026-09-02", 6.71)],
      "sorted (date, rate) rows: %r" % (rows,))
rows2, _ = a5._parse_frank_rates(frank, "EUR")
check(rows2[0] == ("2026-09-01", 0.858), "second currency extracted")
rows3, err3 = a5._parse_frank_rates(dict(rates=dict()), "CNY")
check(rows3 == [] and err3 is not None, "empty rates -> error")

print("[3] _parse_kraken_ohlc")
krak = dict(error=[], result=dict([("XXBTZUSD", [
    [1786208400, "65036.4", "65093.3", "65032.3", "65072.3",
     "65067.2", "24.13", 1412],
    [1786212000, "65072.3", "65100.0", "65040.1", "65090.0",
     "65080.0", "30.5", 1500],
])]))
rows, err = a5._parse_kraken_ohlc(krak)
check(err is None and len(rows) == 2, "2 candles parsed: %s" % (err or rows))
check(rows[0]["ts"] == 1786208400 and rows[0]["close"] == 65072.3,
      "ts + close floats")
check(rows[1]["vwap"] == 65080.0 and rows[1]["volume"] == 30.5
      and rows[1]["count"] == 1500, "vwap + volume + count")
krak_err = dict(error=["EQuery:Unknown asset pair"], result=dict())
rows, err = a5._parse_kraken_ohlc(krak_err)
check(rows is None and err is not None and "Unknown asset" in err,
      "Kraken error payload surfaced")

print("[4] _parse_cb_candles (Coinbase newest-first)")
cb = _json.dumps([
    [1788739200, 79250.0, 80564.24, 79833.86, 80339.13, 2000.39],
    [1788825600, 78666.0, 80462.23, 80339.13, 79084.99, 2461.86],
])
rows, err = a5._parse_cb_candles(cb)
check(err is None and len(rows) == 2, "2 candles: %s" % (err or rows))
check(rows[0]["ts"] == 1788739200, "reversed to oldest-first")
check(rows[0]["low"] == 79250.0 and rows[0]["high"] == 80564.24,
      "Coinbase column order low,high honored")
rows, err = a5._parse_cb_candles("not json")
check(rows is None and err is not None, "malformed -> error")

print("[5] _parse_okx_candles / _parse_okx_funding")
okx = dict(code="0", data=[
    ["1788796800000", "78833.9", "79122.2", "78808.9", "79122.2",
     "121.58", "9598539", "9598539", "1.0"],
    ["1788710400000", "78500.0", "79000.0", "78400.0", "78833.9",
     "130.0", "9800000", "9800000", "1.0"],
])
rows, err = a5._parse_okx_candles(okx)
check(err is None and rows[0]["ts"] == 1788710400000 and rows[0]["open"] == 78500.0,
      "newest-first reversed, floats: %s" % (err or rows[:1]))
rows, err = a5._parse_okx_candles(dict(code="51001", data=[]))
check(rows is None and err is not None, "OKX non-zero code -> error")
okx_f = dict(code="0", data=[
    dict(formulaType="withRate", fundingRate="0.0000305689714203",
         fundingTime="1788796800000", instId="BTC-USDT-SWAP"),
    dict(formulaType="withRate", fundingRate="-0.0000123",
         fundingTime="1788710400000", instId="BTC-USDT-SWAP"),
])
rows, err = a5._parse_okx_funding(okx_f)
check(err is None and rows[0]["ts"] == 1788710400000 and rows[0]["rate"] < 0,
      "funding history reversed with signed rate")

print("[6] _parse_pm_markets (Polymarket)")
pm = [_json.dumps(dict(
    question="Fed cut in Sept?", slug="fed-cut-sept",
    outcomes="[\"Yes\", \"No\"]",
    outcomePrices="[\"0.72\", \"0.28\"]",
    volume24hr="123456.7", liquidityNum=999.5,
    bestBid=0.71, bestAsk=0.73, endDate="2026-09-17",
    closed=False,
))]
rows, err = a5._parse_pm_markets(pm)
check(err is None and len(rows) == 1, "1 market: %s" % (err or rows))
r = rows[0]
check(r["probs"] == dict(Yes=0.72, No=0.28), "outcomePrices JSON -> probs")
check(r["volume24hr"] == 123456.7, "volume float")
check(abs(r["spread"] - 0.02) < 1e-9, "spread = ask - bid")
rows, err = a5._parse_pm_markets([_json.dumps(dict(question="bad"))])
check(err is None and rows[0]["probs"] == dict(), "missing price fields fail-soft")

print("[7] _parse_td_securities (TreasuryDirect auctions)")
td = [
    dict(cusip="91282CRF0", securityType="Note", securityTerm="9-Year 11-Month",
         auctionDate="2026-09-09T00:00:00", issueDate="2026-09-15T00:00:00",
         maturityDate="2036-08-15T00:00:00", offeringAmount="42000000000",
         bidToCoverRatio="2.41", pricePer100="",
         highInvestmentRate="4.650", interestRate="4.625000"),
    dict(cusip="912797UL9", securityType="Bill", securityTerm="6-Week",
         auctionDate="2026-09-08T00:00:00", issueDate="2026-09-10T00:00:00",
         maturityDate="2026-10-22T00:00:00", offeringAmount="70000000000",
         bidToCoverRatio="2.98", pricePer100="99.987222",
         highInvestmentRate="", interestRate=""),
]
rows, err = a5._parse_td_securities(td)
check(err is None and len(rows) == 2, "2 securities: %s" % (err or rows))
check(rows[0]["auction_date"] == "2026-09-09", "sorted newest auction first")
check(rows[0]["interest_rate"] == 4.625 and rows[0]["high_yield"] == 4.65,
      "note coupon + high yield parsed")
check(rows[1]["bid_to_cover"] == 2.98 and rows[1]["price_per_100"] == 99.987222,
      "bill cover + price parsed")
check(rows[0]["price_per_100"] is None, "empty string -> None (unsettled)")
rows, err = a5._parse_td_securities([])
check(rows == [] and err is None, "empty window -> empty, no error")

print("[8] _parse_rss_items (Google News)")
gn = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?><rss version=\"2.0\">"
      "<channel><title>Tesla - Google News</title>"
      "<item><title>Fed hints at cut - Reuters</title>"
      "<link>https://news.google.com/rss/articles/1</link>"
      "<pubDate>Mon, 07 Sep 2026 10:00:00 GMT</pubDate>"
      "<source url=\"https://reuters.com\">Reuters</source></item>"
      "<item><title>NVDA earnings beat - Bloomberg</title>"
      "<link>https://news.google.com/rss/articles/2</link>"
      "<pubDate>Tue, 08 Sep 2026 11:30:00 GMT</pubDate>"
      "<source url=\"https://bloomberg.com\">Bloomberg</source></item>"
      "</channel></rss>")
rows, err = a5._parse_rss_items(gn)
check(err is None and len(rows) == 2, "2 items: %s" % (err or rows))
check(rows[0]["headline"] == "Fed hints at cut" and rows[0]["publisher"] == "Reuters",
      "headline split from publisher: %r" % (rows[0],))
check(rows[1]["pub_date"].startswith("Tue, 08 Sep 2026"), "pubDate kept")
rows, err = a5._parse_rss_items("")
check(rows == [] and err is None, "empty feed -> empty, no error")

print("[9] _parse_atom_entries (Reddit)")
atom = ("<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<feed xmlns=\"http://www.w3.org/2005/Atom\">"
        "<entry><title type=\"text\">DD: squeeze incoming</title>"
        "<link href=\"https://reddit.com/r/wallstreetbets/comments/1\"/>"
        "<updated>2026-09-08T00:10:00+00:00</updated>"
        "<author><name>/u/deepdd</name></author>"
        "<category term=\"DD\"/></entry>"
        "<entry><title>Yolo</title>"
        "<link href=\"https://reddit.com/r/wallstreetbets/comments/2\"/>"
        "<updated>2026-09-08T00:20:00+00:00</updated>"
        "<author><name>/u/yoloer</name></author></entry>"
        "</feed>")
rows, err = a5._parse_atom_entries(atom)
check(err is None and len(rows) == 2, "2 entries: %s" % (err or rows))
check(rows[0]["title"] == "DD: squeeze incoming" and rows[0]["author"] == "/u/deepdd",
      "title + author extracted")
check(rows[0]["link"].endswith("/comments/1"), "link href")
check(rows[0]["updated"] == "2026-09-08T00:10:00+00:00", "updated timestamp")
rows, err = a5._parse_atom_entries("<feed xmlns=\"http://www.w3.org/2005/Atom\"/>")
check(rows == [] and err is None, "empty feed -> empty, no error")

print("[10] _cube_to_rows (Eurostat SDMX-JSON)")
cube = dict(
    value=dict([("0", 2.1), ("1", 2.0)]),
    size=[1, 1, 1, 1, 2],
    id=["freq", "unit", "coicop", "geo", "time"],
    dimension=dict(time=dict(category=dict(index=dict(
        [("2025-11", 0), ("2025-12", 1)])))),
)
rows, err = a5._cube_to_rows(cube)
check(err is None and rows == [("2025-11", 2.1), ("2025-12", 2.0)],
      "cube flattened in time order: %r" % (rows,))
empty_cube = dict(value=dict(), size=[1, 1, 1, 1, 0], id=[],
                  dimension=dict(time=dict(category=dict(index=dict()))))
rows, err = a5._cube_to_rows(empty_cube)
check(rows == [] and err is not None, "empty cube -> error")

print("[11] _bls_series_rows (keyless BLS v1)")
bls = dict(status="REQUEST_SUCCEEDED", message=[],
           Results=dict(series=[dict(
               seriesID="CUSR0000SA0",
               data=[dict(year="2026", period="M07", periodName="July",
                          value="332.813", latest="true"),
                     dict(year="2026", period="M06", periodName="June",
                          value="332.568")])]))
rows, err = a5._bls_series_rows(bls)
check(err is None and len(rows) == 2, "2 obs: %s" % (err or rows))
check(rows[0]["series"] == "CUSR0000SA0" and rows[0]["ym"] == "2026-07"
      and rows[0]["value"] == 332.813, "series + ym + value")
bls_bad = dict(status="REQUEST_FAILED", message=["bad series id"],
               Results=dict(series=[]))
rows, err = a5._bls_series_rows(bls_bad)
check(rows is None and err is not None and "bad series" in err,
      "REQUEST_FAILED -> error with message")

print("[12] _parse_wb (World Bank)")
wb = [
    dict(page=1, pages=1, per_page=5, total=3),
    [
        dict(indicator=dict(id="NY.GDP.MKTP.KD.ZG", value="GDP growth"),
             country=dict(value="United States"), date="2025", value=2.16),
        dict(indicator=dict(id="NY.GDP.MKTP.KD.ZG", value="GDP growth"),
             country=dict(value="United States"), date="2024", value=None),
        dict(indicator=dict(id="NY.GDP.MKTP.KD.ZG", value="GDP growth"),
             country=dict(value="United States"), date="2023", value=2.51),
    ],
]
rows, err = a5._parse_wb(wb)
check(err is None and rows == [("2025", 2.16), ("2023", 2.51)],
      "null values skipped, sorted desc: %r" % (rows,))
rows, err = a5._parse_wb([dict(message=[dict(id="invalid")])])
check(rows is None and err is not None, "WB error payload -> error")

print("[13] _parse_nasdaq_rows")
nq = dict(data=dict(table=dict(
    headers=dict(symbol="Symbol"),
    rows=[
        dict(symbol="NVDA", name="NVIDIA Corporation Common Stock",
             lastsale="$230.36", netchange="1.91", pctchange="0.84%",
             marketCap="5.61T", sector="Technology"),
        dict(symbol="", name=None),
    ])))
rows, err = a5._parse_nasdaq_rows(nq)
check(err is None and len(rows) == 1, "blank rows dropped: %s" % (err or rows))
check(rows[0]["symbol"] == "NVDA" and rows[0]["last_sale"] == 230.36,
      "price dollar-sign stripped")

print("[14] fail-closed JSON fetchers")
STUB.on("frankfurter.app", "{not json")
rows, err = a5.fx_history("CNY", start="2026-09-01", end="2026-09-02")
check(rows is None and err is not None, "malformed frankfurter -> error")
STUB.on("gamma-api.polymarket.com", "[{broken")
rows, err = a5.polymarket_markets(limit=1)
check(rows is None and err is not None, "malformed polymarket -> error")

print()
print("sweep jobs present:")
for name in ("fx_snapshot", "kraken_ohlc", "coinbase_candles", "okx_candles",
             "okx_funding_history", "polymarket_markets", "treasury_auctions",
             "google_news", "reddit_top", "eurostat_hicp", "bls_series",
             "worldbank_indicator", "nasdaq_universe", "alt_data_sweep"):
    check(callable(getattr(a5, name, None)), "%s callable" % name)

print()
if failures:
    print("FAILED (%d):" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
