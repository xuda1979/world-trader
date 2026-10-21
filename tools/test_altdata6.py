"""TDD tests for wt.altdata6 (new keyless free data sources, 2026-09-08).

Run: python3 tools/test_altdata6.py
Exits 0 on pass, 1 on any failure. OFFLINE: all network calls are stubbed;
synthetic payloads verify parsing and fail-closed invariants only.
Fixture shapes are transcribed from live probes of each endpoint on
2026-09-08 (field names and nesting are real, values are synthetic).
No synthetic PnL claims (2026-07-26 policy).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from wt import altdata6 as a6

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
a6._clean_get_orig = a6._clean_get
a6._clean_post_orig = a6._clean_post


def _fake_clean_get(url, **kw):
    value, exc = STUB.find(url)
    if exc is not None:
        return None, a6.describe_err(exc)
    if isinstance(value, Exception):
        return None, a6.describe_err(value)
    return value, None


def _fake_clean_post(url, *, body=None, **kw):
    return _fake_clean_get(url, **kw)


def _fake_clean_json(url, **kw):
    txt, e = _fake_clean_get(url, **kw)
    if e:
        return None, e
    try:
        import json
        return json.loads(txt), None
    except Exception as e:
        return None, a6.describe_err(e)


a6._clean_get = _fake_clean_get
a6._clean_post = _fake_clean_post
a6._clean_json = _fake_clean_json

import json as _json


def _j(obj):
    return _json.dumps(obj)


print("[1] _f numeric coercion")
check(a6._f("4.625000") == 4.625, "string float parsed")
check(a6._f("") is None, "empty string -> None")
check(a6._f(None) is None, "None -> None")
check(a6._f("n/a") is None, "junk -> None")
check(a6._f(12) == 12.0, "int passthrough")
check(a6._f("1,313.00") == 1313.0, "thousands separator stripped")
check(a6._f("+0.84%") == 0.84, "signed percent stripped")
check(a6._f("$28,065,267,700") == 28065267700.0, "dollar mcap stripped")

print("[2] _parse_cnbc_quotes (CNBC restQuote -- Yahoo replacement)")
cnbc = dict(FormattedQuoteResult=dict(FormattedQuote=[
    dict(symbol="600519.SS", code=0, name="Kweichow Moutai Co., Ltd.",
         last="1,313.00", change="-3.01", change_pct="-0.23%",
         high="1,323.00", low="1,312.81", open="1,318.00",
         previous_day_closing="1,316.01", volume="626,064",
         currencyCode="CNY", exchange="Shanghai Stock Exchange",
         last_time="2026-09-08T10:27:00.000+0800", realTime="false",
         pe="20.19", mktcapView="1.641T", eps="65.04",
         dividendyield="3.96%", countryCode="CN", type="STOCK"),
    dict(symbol="BAD.SS", code=1),
    dict(symbol="EUR=", code=0, name="EUR/USD", last="1.1624",
         change="+0.0258%", change_pct="+0.0258%", high="1.1634",
         low="1.1622", type="CURRENCY"),
]))
rows, err = a6._parse_cnbc_quotes(cnbc)
check(err is None and len(rows) == 2, "code=0 rows kept, misses dropped: %s"
      % (err or rows))
moutai = rows[0]
check(moutai["symbol"] == "600519.SS" and moutai["last"] == 1313.0,
      "comma-thousands last parsed")
check(moutai["change_pct"] == -0.23 and moutai["change"] == -3.01,
      "signed pct change parsed")
check(moutai["high"] == 1323.0 and moutai["volume"] == 626064,
      "high + volume floats")
check(moutai["pe"] == 20.19 and moutai["mktcap_view"] == "1.641T",
      "fundamentals parsed")
check(moutai["prev_close"] == 1316.01 and moutai["currency"] == "CNY",
      "prev close + currency kept")
fx = rows[1]
check(fx["last"] == 1.1624 and fx["change_pct"] == 0.0258, "FX quote parsed")
rows, err = a6._parse_cnbc_quotes(dict(FormattedQuoteResult=dict(
    FormattedQuote=[dict(symbol="X", code=1)])))
check(rows == [] and err is None, "all-miss batch -> empty list, not error")
rows, err = a6._parse_cnbc_quotes(dict(nope=1))
check(rows is None and err is not None, "malformed payload -> error")

print("[3] _parse_ff_calendar (ForexFactory weekly econ calendar)")
ff = [
    dict(title="ANZ Job Advertisements m/m", country="AUD",
         date="2026-09-06T21:30:00-04:00", impact="Low",
         forecast="", previous="0.8%"),
    dict(title="FOMC Statement", country="USD",
         date="2026-09-09T14:00:00-04:00", impact="High",
         forecast="4.00%", previous="4.25%"),
    dict(title="CPI y/y", country="USD",
         date="2026-09-11T08:30:00-04:00", impact="High",
         forecast="2.9%", previous="2.8%"),
]
rows, err = a6._parse_ff_calendar(ff, min_impact=None)
check(err is None and len(rows) == 3, "no filter -> all rows: %s"
      % (err or rows))
rows, err = a6._parse_ff_calendar(ff, min_impact="High")
check(err is None and len(rows) == 2
      and rows[0]["title"] == "FOMC Statement", "High-impact filter")
check(rows[0]["date"] == "2026-09-09T14:00:00-04:00", "ISO date kept")
check(rows[0]["currency"] == "USD" and rows[0]["forecast"] == "4.00%",
      "currency + forecast kept")
rows, err = a6._parse_ff_calendar([], min_impact=None)
check(rows == [] and err is None, "empty week -> empty, no error")


print("[4] _parse_nasdaq_calendar rows (earnings/dividends/ipo)")
earn = dict(data=dict(asOf="Tue, Sep 8, 2026", headers=dict(),
                      rows=[dict(lastYearRptDt="9/08/2025",
                                 lastYearEPS="$5.77",
                                 time="time-after-hours", symbol="CASY",
                                 name="Caseys General Stores, Inc.",
                                 marketCap="$28,065,267,700",
                                 fiscalQuarterEnding="Jul/2026",
                                 epsForecast="$6.60", noOfEsts="7")]))
rows, err = a6._parse_nasdaq_earnings(earn)
check(err is None and rows[0]["symbol"] == "CASY", "earnings row: %s"
      % (err or rows))
check(rows[0]["eps_forecast"] == 6.6
      and rows[0]["market_cap"] == 28065267700.0, "dollar strings coerced")
check(rows[0]["time"] == "time-after-hours", "bmo/amc kept")

div = dict(data=dict(calendar=dict(asOf="Tue, Sep 8, 2026", headers=dict(),
                                   rows=[dict(companyName="Avantis Credit ETF",
                                              symbol="AVGB",
                                              dividend_Ex_Date="9/08/2026",
                                              payment_Date="9/10/2026",
                                              record_Date="9/08/2026",
                                              dividend_Rate=0.5015,
                                              indicated_Annual_Dividend=1.0828,
                                              announcement_Date="9/04/2026")])))
rows, err = a6._parse_nasdaq_dividends(div)
check(err is None and rows[0]["symbol"] == "AVGB", "dividend row: %s"
      % (err or rows))
check(rows[0]["dividend_rate"] == 0.5015
      and rows[0]["annual_dividend"] == 1.0828, "rates numeric")

ipo = dict(data=dict(year=2026, month=9, totalResults=2,
                     priced=dict(asOf=None, headers=dict(),
                                 rows=[dict(dealID="1371606-117318",
                                            proposedTickerSymbol="TRBG",
                                            companyName="Turbogen Ltd.",
                                            proposedExchange="NASDAQ Capital",
                                            proposedSharePrice=None,
                                            sharesOffered="2,066,243",
                                            pricedDate="9/03/2026",
                                            dealStatus="Priced")]),
                     upcoming=dict(lastUpdatedTime="...",
                                   upcomingTable=dict(headers=dict(),
                                                      rows=[dict(
                                                          dealID="1397270",
                                                          proposedTickerSymbol="PTT",
                                                          companyName="SIYATA PTT",
                                                          expectedPriceDate="9/08/2026",
                                                          dealStatus="Expected")])),
                     withdrawn=dict(rows=[]), filed=dict(rows=[])))
rows, err = a6._parse_nasdaq_ipo(ipo)
check(err is None and len(rows) == 2, "priced + upcoming merged: %s"
      % (err or rows))
check(rows[0]["symbol"] == "TRBG" and rows[0]["status"] == "Priced"
      and rows[0]["kind"] == "priced", "priced row tagged")
check(rows[1]["symbol"] == "PTT" and rows[1]["kind"] == "upcoming",
      "upcoming row tagged")
check(rows[0]["shares_offered"] == 2066243, "shares coerced")

print("[5] _parse_stablecoins (DeFiLlama flows)")
sc = dict(peggedAssets=[
    dict(id="1", name="Tether", symbol="USDT", pegType="peggedUSD",
         pegMechanism="fiat-backed",
         circulating=dict(peggedUSD=183374848274.99),
         circulatingPrevDay=dict(peggedUSD=183351265965.77),
         circulatingPrevWeek=dict(peggedUSD=183466863328.94),
         circulatingPrevMonth=dict(peggedUSD=183186493581.93)),
    dict(id="2", name="USDC", symbol="USDC", pegType="peggedUSD",
         pegMechanism="fiat-backed",
         circulating=dict(peggedUSD=72000000000.0),
         circulatingPrevDay=dict(peggedUSD=71500000000.0)),
    dict(id="3", name="DAI", symbol="DAI", pegType="peggedUSD",
         pegMechanism="overcollateralized",
         circulating=dict(peggedUSD=5000000000.0)),
])
rows, err = a6._parse_stablecoins(sc)
check(err is None and len(rows) == 3, "3 stables: %s" % (err or rows))
check(rows[0]["symbol"] == "USDT"
      and rows[0]["circulating"] == 183374848274.99, "sorted by mcap desc")
usdt = rows[0]
check(abs(usdt["flow_1d"] - 23582309.22) < 1.0, "1d flow computed")
check(abs(usdt["flow_1w"] + 92015053.95) < 1.0, "1w flow signed")
usdc = rows[1]
check(abs(usdc["flow_1d"] - 500000000.0) < 0.01, "USDC 1d flow")
check(usdc["flow_1w"] is None, "missing prevWeek -> None, not crash")
dai = rows[2]
check(dai["flow_1d"] is None and dai["flow_1m"] is None,
      "no history -> all flows None")
rows, err = a6._parse_stablecoins(dict(peggedAssets=[]))
check(rows == [] and err is not None, "empty roster -> error")

print("[6] _parse_dvol (Deribit volatility index candles)")
dvol = dict(jsonrpc="2.0", result=dict(data=[
    [1757116800000, 37.49, 38.03, 37.04, 37.76],
    [1757203200000, 37.76, 37.90, 37.43, 37.90]], continuation=None))
rows, err = a6._parse_dvol(dvol)
check(err is None and len(rows) == 2, "2 DVOL bars: %s" % (err or rows))
check(rows[0]["ts"] == 1757116800000 and rows[0]["close"] == 37.76,
      "ts + close parsed")
check(rows[0]["high"] == 38.03 and rows[0]["low"] == 37.04,
      "o,h,l,c order honored")
check(rows[1]["open"] == 37.76, "open parsed")
rows, err = a6._parse_dvol(dict(result=dict(data=[])))
check(rows is None and err is not None, "empty DVOL -> error")

print("[7] _parse_deribit_options (book summary)")
opts = dict(jsonrpc="2.0", result=[
    dict(instrument_name="BTC-25SEP26-105000-C", mark_price=0.00038446,
         volume=1.2, open_interest=1538.2, bid_price=0.0003, ask_price=0.0005,
         underlying_price=79215.71, interest_rate=0.0),
    dict(instrument_name="BTC-25SEP26-90000-P", mark_price=0.0,
         volume=None, open_interest=0.0, bid_price=None, ask_price=0.0001,
         underlying_price=79215.71, interest_rate=0.0),
    dict(instrument_name="BTC-PERPETUAL", mark_price=79215.0, volume=3141.0,
         open_interest=60000.0, bid_price=None, ask_price=None,
         underlying_price=79215.71, interest_rate=0.0),
])
rows, err = a6._parse_deribit_options(opts, min_oi=1.0)
check(err is None and len(rows) == 1, "zero-OI + perp filtered: %s"
      % (err or rows))
o = rows[0]
check(o["expiry"] == "25SEP26" and o["strike"] == 105000.0
      and o["right"] == "C", "instrument_name parsed into legs")
check(o["mark"] == 0.00038446 and o["open_interest"] == 1538.2,
      "mark + OI floats")
check(o["underlying"] == 79215.71, "underlying kept")
rows, err = a6._parse_deribit_options(opts, min_oi=0.0)
check(len(rows) == 2 and rows[0]["strike"] >= rows[1]["strike"],
      "min_oi=0 keeps thin strikes, strike-sorted")
rows, err = a6._parse_deribit_options(opts, min_oi=1.0, right="P")
check(rows == [] and err is None, "right filter miss -> empty, no error")


print("[8] _parse_stocktwits (symbol stream + sentiment tally)")
stw = dict(symbol=dict(symbol="NVDA", id=2925), cursor=dict(more=True),
           messages=[
    dict(id=663763555, created_at="2026-09-08T02:41:16Z",
         body="$NVDA What goes up must crash to 0",
         user=dict(username="BuySellHoldFinance", followers=100, ideas=3),
         entities=dict(sentiment=dict(basic="Bearish"))),
    dict(id=663763556, created_at="2026-09-08T02:42:16Z",
         body="DD: squeeze incoming",
         user=dict(username="deepdd", followers=500, ideas=10),
         entities=dict(sentiment=dict(basic="Bullish"))),
    dict(id=663763557, created_at="2026-09-08T02:43:16Z",
         body="no opinion here",
         user=dict(username="lurker", followers=1, ideas=0),
         entities=dict()),
])
rows, err = a6._parse_stocktwits(stw)
check(err is None and len(rows) == 3, "3 messages: %s" % (err or rows))
check(rows[0]["sentiment"] == "Bearish" and rows[1]["sentiment"] == "Bullish"
      and rows[2]["sentiment"] is None, "sentiment extracted, None default")
check(rows[0]["user"] == "BuySellHoldFinance", "username kept")
tally = a6.sentiment_tally(rows)
check(tally == dict(n=3, bullish=1, bearish=1, unlabeled=1),
      "tally counts: %r" % (tally,))

print("[9] _parse_mempool_fees")
mp = dict(fastestFee=2, halfHourFee=1, hourFee=1, economyFee=1, minimumFee=1)
rows, err = a6._parse_mempool_fees(mp)
check(err is None and rows["fastest_fee"] == 2 and rows["minimum_fee"] == 1,
      "fees mapped: %r" % (rows,))
rows, err = a6._parse_mempool_fees(dict(unexpected=1))
check(rows is None and err is not None, "unexpected payload -> error")

print("[10] _parse_nhc_storms")
nhc = dict(activeStorms=[
    dict(id="ep132026", binNumber="EP3", name="Marie", classification="TS",
         intensity="45", pressure="994", latitude="25.1N", longitude="115.2W",
         movement="None", publicAdvisory=dict(advNum="028")),
])
rows, err = a6._parse_nhc_storms(nhc)
check(err is None and len(rows) == 1, "1 storm: %s" % (err or rows))
check(rows[0]["intensity_kt"] == 45 and rows[0]["pressure_hpa"] == 994,
      "intensity_kt/pressure_hpa coerced from strings")
check(rows[0]["classification"] == "TS" and rows[0]["lat"] == "25.1N",
      "classification + lat kept")
rows, err = a6._parse_nhc_storms(dict(activeStorms=[]))
check(rows == [] and err is None, "no active storms -> empty, no error")

print("[11] _parse_gtrends (Trending Now RSS)")
gt = ("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
      "<rss xmlns:ht=\"https://trends.google.com/trending/rss\" version=\"2.0\">"
      "<channel><title>Daily Search Trends</title>"
      "<item><title>toronto blue jays</title>"
      "<ht:approx_traffic>500+</ht:approx_traffic>"
      "<link>https://trends.google.com/trending/rss?geo=US</link>"
      "<pubDate>Mon, 7 Sep 2026 19:30:00 -0700</pubDate>"
      "<ht:news_item_title>Kyle Isbel reaches on error</ht:news_item_title>"
      "<ht:news_item_url>https://www.mlb.com/video/x</ht:news_item_url></item>"
      "<item><title>market selloff</title>"
      "<ht:approx_traffic>20K+</ht:approx_traffic>"
      "<link>https://trends.google.com/trending/rss?geo=US</link>"
      "<pubDate>Mon, 7 Sep 2026 19:40:00 -0700</pubDate></item>"
      "</channel></rss>")
rows, err = a6._parse_gtrends(gt)
check(err is None and len(rows) == 2, "2 trends: %s" % (err or rows))
check(rows[0]["title"] == "market selloff" and rows[0]["traffic_n"] == 20000,
      "20K+ traffic coerced, sorted desc")
check(rows[1]["title"] == "toronto blue jays"
      and rows[1]["traffic_n"] == 500, "title + numeric traffic")
check(rows[1]["news_title"] == "Kyle Isbel reaches on error",
      "news item extracted")
rows, err = a6._parse_gtrends("<rss version=\"2.0\"><channel/></rss>")
check(rows == [] and err is None, "empty feed -> empty, no error")

print("[12] _parse_bitget_tickers")
bg = dict(code="00000", msg="success", requestTime=1788835840512, data=[
    dict(symbol="BTCUSDT", lastPr="79085.8", askPr="79085.9", bidPr="79085.8",
         high24h="80212.2", low24h="78644.8", ts="1788835840512",
         change24h="-0.01385", baseVolume="21049.5838",
         usdtVolume="1668387317.06007", openUtc="79076.5",
         changeUtc24h="0.00012", indexPrice="79115.7795",
         fundingRate="0.000062", holdingAmount="33641.62",
         open24h="80196.3", markPrice="79085.8"),
    dict(symbol="ETHUSDT", lastPr="2492.9", fundingRate="-0.0001",
         change24h="0.011", usdtVolume="900000000.0", markPrice="2492.9",
         indexPrice="2493.1", holdingAmount="100000.0"),
])
rows, err = a6._parse_bitget_tickers(bg)
check(err is None and len(rows) == 2, "2 tickers: %s" % (err or rows))
check(rows[0]["symbol"] == "BTCUSDT" and rows[0]["last"] == 79085.8,
      "last coerced")
check(rows[0]["funding_rate"] == 0.000062, "funding rate parsed")
check(rows[1]["funding_rate"] < 0, "negative funding preserved")
check(rows[0]["mark"] == 79085.8 and rows[0]["index"] == 79115.7795,
      "mark + index price")
bg_bad = dict(code="40001", msg="bad productType", data=[])
rows, err = a6._parse_bitget_tickers(bg_bad)
check(rows is None and err is not None, "non-zero code -> error")

print("[13] _parse_finra_csi (consolidated short interest, CSV via POST)")
finra_csv = (
    '"accountingYearMonthNumber","symbolCode","issueName",'
    '"issuerServicesGroupExchangeCode","marketClassCode",'
    '"currentShortPositionQuantity","previousShortPositionQuantity",'
    '"stockSplitFlag","averageDailyVolumeQuantity","daysToCoverQuantity",'
    '"revisionFlag","changePercent","changePreviousNumber","settlementDate"\n'
    '"20260715","A","Agilent Technologies Inc.","A","NYSE","7538437",'
    '"5331733",,"2136993","3.53",,"41.39","2206704","2026-07-15"\n'
    '"20260715","AA","Alcoa Corporation","A","NYSE","8981785","8425769",,'
    '"6969483","1.29",,"6.60","556016","2026-07-15"\n')
rows, err = a6._parse_finra_csi(finra_csv)
check(err is None and len(rows) == 2, "2 CSI rows: %s" % (err or rows))
check(rows[0]["symbol"] == "A" and rows[0]["short_pos"] == 7538437,
      "short position coerced")
check(rows[0]["days_to_cover"] == 3.53 and rows[0]["chg_pct"] == 41.39,
      "days-to-cover + change parsed")
check(rows[0]["settlement"] == "2026-07-15", "settlement date kept")
check(rows[1]["avg_vol"] == 6969483, "avg volume coerced")
rows, err = a6._parse_finra_csi("")
check(rows == [] and err is not None, "empty CSV -> error")
rows, err = a6._parse_finra_csi("error,message\n\"bad request\",\"x\"\n")
check(rows is None and err is not None, "FINRA error CSV -> error")

print("[14] _parse_ecb_series (SDMX csvdata)")
ecb_csv = (
    "KEY,FREQ,CURRENCY,CURRENCY_DENOM,EXR_TYPE,EXR_SUFFIX,TIME_PERIOD,"
    "OBS_VALUE,OBS_STATUS\n"
    "EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-09-01,1.1567,\n"
    "EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-09-02,1.1601,\n"
    "EXR.D.USD.EUR.SP00.A,D,USD,EUR,SP00,A,2026-09-03,,A\n")
rows, err = a6._parse_ecb_series(ecb_csv)
check(err is None and rows == [("2026-09-01", 1.1567),
                               ("2026-09-02", 1.1601)],
      "rows sorted, missing obs dropped: %r" % (rows,))
rows, err = a6._parse_ecb_series("")
check(rows == [] and err is not None, "empty payload -> ([], err)")

print("[15] fetchers fail-closed on malformed payloads")
STUB.on("restQuote", "not json at all")
rows, err = a6.cnbc_quotes(["NVDA"])
check(rows is None and err is not None, "malformed cnbc -> error")
STUB.on("ff_calendar_thisweek", "[broken")
rows, err = a6.ff_calendar()
check(rows is None and err is not None, "malformed ff -> error")
STUB.on("stablecoins.llama.fi", "bad json")
rows, err = a6.stablecoin_flows()
check(rows is None and err is not None, "malformed stablecoins -> error")
STUB.on("get_volatility_index_data", "bad json")
rows, err = a6.deribit_dvol("BTC")
check(rows is None and err is not None, "malformed dvol -> error")
STUB.on("get_book_summary_by_currency", "bad json")
rows, err = a6.deribit_options("BTC")
check(rows is None and err is not None, "malformed options -> error")
STUB.on("streams/symbol", "bad json")
rows, err = a6.stocktwits_stream("NVDA")
check(rows is None and err is not None, "malformed stocktwits -> error")
STUB.on("trending/rss", "<not closed")
rows, err = a6.google_trends("US")
check(rows is None and err is not None, "malformed trends -> error")
STUB.on("mix/market/tickers", "bad json")
rows, err = a6.bitget_tickers()
check(rows is None and err is not None, "malformed bitget -> error")
STUB.on("consolidatedShortInterest", "")
rows, err = a6.finra_short_interest()
check(rows is None and err is not None, "malformed finra -> error")
STUB.on("service/data", "not csv at all")
rows, err = a6.ecb_series("EXR/D.USD.EUR.SP00.A")
check(rows is None and err is not None, "malformed ecb -> error")

print()
print("sweep jobs present:")
for name in ("cnbc_quotes", "ff_calendar", "nasdaq_earnings", "nasdaq_ipo",
             "nasdaq_dividends", "stablecoin_flows", "deribit_dvol",
             "deribit_options", "stocktwits_stream", "mempool_fees",
             "nhc_storms", "google_trends", "bitget_tickers",
             "finra_short_interest", "ecb_series", "alt_data_sweep"):
    check(callable(getattr(a6, name, None)), "%s callable" % name)

print()
if failures:
    print("FAILED (%d):" % len(failures))
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
