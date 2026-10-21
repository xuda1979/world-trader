"""altdata6 -- new free data sources added 2026-09-08 (batch 6).

All sources here are FREE and need NO API key. Each fetcher returns
(data, err) consistent with the rest of the package.

Sources in this module (all verified live from this env on 2026-09-08;
everything goes through _clean_get/_clean_post, same flaky-proxy caveat
as altdata3/4/5):

  - CNBC restQuote                  -> multi-asset quotes in ONE call:
                                       US equities, China A-shares
                                       (600519.SS), HK (0700.HK), indices
                                       (.SPX/.IXIC), COMEX/NYMEX futures
                                       (@GC.1/@CL.1), yields (US2Y/US10Y),
                                       FX (EUR=/GBP=), crypto (BTC=/ETH=).
                                       THE Yahoo/Stooq replacement for
                                       cross-asset spot quotes.
  - ForexFactory (faireconomy)      -> this-week economic calendar with
                                       impact ratings (event-risk radar).
  - Nasdaq calendars                -> earnings (with EPS estimates),
                                       IPO priced + upcoming, dividends.
  - DeFiLlama stablecoins           -> circulating supply + 1d/1w/1m flows
                                       (stablecoin mint/burn = crypto
                                       liquidity on/off-ramp).
  - Deribit DVOL + options chain    -> crypto implied-vol index + full
                                       options surface (mark, OI).
  - Stocktwits symbol stream        -> tagged Bullish/Bearish sentiment.
  - mempool.space                   -> BTC fee market (on-chain stress).
  - NHC CurrentStorms               -> active hurricane tracks (energy/
                                       insurance risk).
  - Google Trends RSS               -> trending searches w/ traffic volume
                                       (retail attention radar).
  - Bitget USDT-FUTURES tickers     -> perps across ~200 pairs with funding
                                       + open interest in one call.
  - FINRA consolidatedShortInterest -> exchange-wide short interest with
                                       days-to-cover (POST API; CSV only --
                                       format=json is NOT honored).
  - ECB Data Portal (SDMX csvdata)  -> ECB reference FX + policy rates
                                       (MRR) -- institutional grade,
                                       complements Frankfurter.

Probed and REJECTED on 2026-09-08 (blocked/broken from this env, do not
re-probe without VPN): IMF dataservices.imf.org (SSL UNEXPECTED_EOF on
every attempt), OECD SDMX (404 on all dataflow paths tried), Bank of
England boeapps iadb CSV (returns the site chrome HTML, no CSV), FMP demo
key (401), Bybit v5 (403 Forbidden from this env), CNBC ts.api chart host
(SSL UNEXPECTED_EOF -- quotes work, candle history does not), UMich
consumer sentiment files (HTML page, not CSV).
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, http_post, describe_err

import csv as _csv
import datetime as _dt
import io as _io
import json as _json
import re as _re
import time as _time
import urllib.parse as _urlparse
import xml.etree.ElementTree as _ET

_urlparse_quote = _urlparse.quote

# ---------------------------------------------------------------------------
# Resilient fetch helpers (same rationale as altdata3/4/5: this network has
# a flaky transparent proxy that intermittently serves a captive-portal page).
# ---------------------------------------------------------------------------
_PORTAL_RE = _re.compile("\u7528\u6237\u8ba4\u8bc1\u7cfb\u7edf|\u8ba4\u8bc1\u7cfb\u7edf|\u4e2a\u4eba\u8ba4\u8bc1|\u767b\u5f55\u9a8c\u8bc1")

_BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def _clean_get(url, *, headers=None, timeout=15, retries=3):
    last_err = None
    h = dict(headers) if headers else dict()
    h.setdefault("User-Agent", _BROWSER_UA)
    for attempt in range(retries):
        try:
            txt = http_get(url, headers=h, timeout=timeout)
            if _PORTAL_RE.search(txt):
                last_err = "captive-portal"
                _time.sleep(0.4 * (attempt + 1))
                continue
            return txt, None
        except Exception as e:
            last_err = describe_err(e)
            _time.sleep(0.4 * (attempt + 1))
    return None, last_err


def _clean_post(url, *, body=None, headers=None, timeout=15, retries=3):
    last_err = None
    h = dict(headers) if headers else dict()
    h.setdefault("User-Agent", _BROWSER_UA)
    for attempt in range(retries):
        try:
            txt = http_post(url, headers=h, body=body, timeout=timeout)
            if _PORTAL_RE.search(txt):
                last_err = "captive-portal"
                _time.sleep(0.4 * (attempt + 1))
                continue
            return txt, None
        except Exception as e:
            last_err = describe_err(e)
            _time.sleep(0.4 * (attempt + 1))
    return None, last_err


def _clean_json(url, **kw):
    txt, e = _clean_get(url, **kw)
    if e:
        return None, e
    try:
        return _json.loads(txt), None
    except Exception as e:
        return None, describe_err(e)


def _f(x):
    """Fail-soft numeric coercion: "4.625" -> 4.625; ""/None/junk -> None."""
    if x is None:
        return None
    try:
        return float(str(x).strip().replace(",", "").replace("$", "")
                     .replace("%", ""))
    except (TypeError, ValueError):
        return None


# ============================================================================
# CNBC restQuote -- multi-asset quotes in ONE call. The Yahoo/Stooq
#   replacement: US equities, China A-shares (600519.SS), HK (0700.HK),
#   indices (.SPX/.IXIC), futures (@GC.1 gold, @CL.1 WTI), yields
#   (US2Y/US10Y -- "last" carries a trailing %), FX (EUR=/GBP=), crypto
#   (BTC=/ETH=). Misses come back with code=1 (kept out of the rows).
#   NOTE: ts.api.cnbc.com (candle history) is SSL-dead from this env;
#   quote.cnbc.com answers fine.
#   https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol
#     ?symbols=NVDA|600519.SS|.SPX|@GC.1|US10Y|EUR=&requestMethod=itv
#     &noform=1&partnerId=2&fund=1&output=json
# ============================================================================
def _parse_cnbc_quotes(d):
    quotes = (((d.get("FormattedQuoteResult") or dict())
               .get("FormattedQuote")))
    if quotes is None:
        return None, "unexpected CNBC payload"
    rows = []
    for q in quotes:
        if not isinstance(q, dict) or q.get("code") != 0:
            continue
        rows.append(dict(
            symbol=q.get("symbol"),
            name=q.get("name"),
            last=_f(q.get("last")),
            change=_f(q.get("change")),
            change_pct=_f(q.get("change_pct")),
            open=_f(q.get("open")),
            high=_f(q.get("high")),
            low=_f(q.get("low")),
            prev_close=_f(q.get("previous_day_closing")),
            volume=_f(q.get("volume")),
            currency=q.get("currencyCode"),
            exchange=q.get("exchange"),
            last_time=q.get("last_time"),
            real_time=q.get("realTime") == "true",
            pe=_f(q.get("pe")),
            eps=_f(q.get("eps")),
            dividend_yield=_f(q.get("dividendyield")),
            mktcap_view=q.get("mktcapView"),
            country=q.get("countryCode"),
            kind=q.get("type"),
        ))
    return rows, None


def cnbc_quotes(symbols):
    """Batch quotes. Symbols use CNBC's dialect: NVDA, 600519.SS, 0700.HK,
    .SPX, .IXIC, @GC.1, @CL.1, US2Y, US10Y, EUR=, GBP=, BTC=, ETH=.
    There is no documented limit; batches of <=40 are well-behaved."""
    syms = "|".join(s.strip() for s in symbols if s and s.strip())
    if not syms:
        return None, "no symbols given"
    url = ("https://quote.cnbc.com/quote-html-webservice/restQuote"
           "/symbolType/symbol?symbols=%s&requestMethod=itv&noform=1"
           "&partnerId=2&fund=1&output=json" % _urlparse_quote(syms,
                                                              safe="|"))
    d, e = _clean_json(url, timeout=25)
    if e:
        return None, e
    return _parse_cnbc_quotes(d)


# ============================================================================
# ForexFactory weekly economic calendar (faireconomy.media CDN -- no HTML).
#   https://nfs.faireconomy.media/ff_calendar_thisweek.json
# impact: High | Medium | Low | Holiday. date is ISO with offset.
# ============================================================================
_IMPACT_RANK = dict(Low=1, Medium=2, High=3)


def _parse_ff_calendar(d, min_impact=None):
    if not isinstance(d, list):
        return None, "unexpected FF calendar payload"
    floor = _IMPACT_RANK.get(min_impact or "", 0)
    rows = []
    for ev in d:
        if not isinstance(ev, dict):
            continue
        impact = ev.get("impact")
        if floor and _IMPACT_RANK.get(impact, 0) < floor:
            continue
        rows.append(dict(
            title=ev.get("title"),
            currency=ev.get("country"),
            date=ev.get("date"),
            impact=impact,
            forecast=ev.get("forecast") or None,
            previous=ev.get("previous") or None,
        ))
    rows.sort(key=lambda r: r.get("date") or "")
    return rows, None


def ff_calendar(week="thisweek", min_impact=None):
    """week: thisweek | nextweek | thismonth. min_impact: High|Medium|Low."""
    d, e = _clean_json(
        "https://nfs.faireconomy.media/ff_calendar_%s.json"
        % _urlparse_quote(week), timeout=25)
    if e:
        return None, e
    return _parse_ff_calendar(d, min_impact=min_impact)


# ============================================================================
# Nasdaq calendars: earnings, dividends, IPO (priced + upcoming).
#   https://api.nasdaq.com/api/calendar/earnings?date=YYYY-MM-DD
#   https://api.nasdaq.com/api/calendar/dividends?date=YYYY-MM-DD
#   https://api.nasdaq.com/api/ipo/calendar?date=YYYY-MM
# Dollar/percent strings everywhere -> _f. IPO merges the priced and
# upcoming tables and tags each row.
# ============================================================================
def _parse_nasdaq_earnings(d):
    rows_src = (((d.get("data") or dict()).get("rows")) or [])
    if not rows_src:
        return [], None
    rows = []
    for r in rows_src:
        rows.append(dict(
            symbol=(r.get("symbol") or "").strip(),
            name=r.get("name"),
            eps_forecast=_f(r.get("epsForecast")),
            eps_last_year=_f(r.get("lastYearEPS")),
            last_year_rpt_dt=r.get("lastYearRptDt"),
            fiscal_quarter=r.get("fiscalQuarterEnding"),
            n_estimates=int(_f(r.get("noOfEsts")) or 0),
            market_cap=_f(r.get("marketCap")),
            time=r.get("time"),
        ))
    return [r for r in rows if r["symbol"]], None


def nasdaq_earnings(date=None):
    date = date or _dt.date.today().isoformat()
    d, e = _clean_json(
        "https://api.nasdaq.com/api/calendar/earnings?date=%s"
        % _urlparse_quote(date), timeout=25)
    if e:
        return None, e
    return _parse_nasdaq_earnings(d)


def _parse_nasdaq_dividends(d):
    rows_src = ((((d.get("data") or dict()).get("calendar") or dict())
                 .get("rows")) or [])
    if not rows_src:
        return [], None
    rows = []
    for r in rows_src:
        rows.append(dict(
            symbol=(r.get("symbol") or "").strip(),
            name=r.get("companyName"),
            ex_date=r.get("dividend_Ex_Date"),
            payment_date=r.get("payment_Date"),
            record_date=r.get("record_Date"),
            dividend_rate=_f(r.get("dividend_Rate")),
            annual_dividend=_f(r.get("indicated_Annual_Dividend")),
            announced=r.get("announcement_Date"),
        ))
    return [r for r in rows if r["symbol"]], None


def nasdaq_dividends(date=None):
    date = date or _dt.date.today().isoformat()
    d, e = _clean_json(
        "https://api.nasdaq.com/api/calendar/dividends?date=%s"
        % _urlparse_quote(date), timeout=25)
    if e:
        return None, e
    return _parse_nasdaq_dividends(d)


def _parse_nasdaq_ipo(d):
    data = d.get("data") or dict()
    rows = []
    for r in (((data.get("priced") or dict()).get("rows")) or []):
        rows.append(dict(
            symbol=(r.get("proposedTickerSymbol") or "").strip(),
            name=r.get("companyName"),
            exchange=r.get("proposedExchange"),
            price=_f(r.get("proposedSharePrice")),
            shares_offered=_f(r.get("sharesOffered")),
            date=r.get("pricedDate"),
            status=r.get("dealStatus"),
            kind="priced"))
    for r in (((((data.get("upcoming") or dict())
                 .get("upcomingTable")) or dict()).get("rows")) or []):
        rows.append(dict(
            symbol=(r.get("proposedTickerSymbol") or "").strip(),
            name=r.get("companyName"),
            exchange=r.get("proposedExchange"),
            price=_f(r.get("proposedSharePrice")),
            shares_offered=_f(r.get("sharesOffered")),
            date=r.get("expectedPriceDate"),
            status=r.get("dealStatus"),
            kind="upcoming"))
    return [r for r in rows if r["symbol"]], None


def nasdaq_ipo(year=None, month=None):
    today = _dt.date.today()
    ym = "%s-%02d" % (year or today.year, month or today.month)
    d, e = _clean_json(
        "https://api.nasdaq.com/api/ipo/calendar?date=%s" % ym, timeout=25)
    if e:
        return None, e
    return _parse_nasdaq_ipo(d)


# ============================================================================
# DeFiLlama stablecoins -- circulating supply + 1d/1w/1m net flows. Stable
#   mint/burn is the crypto on/off-ramp liquidity signal (USDT+USDC growth
#   precedes risk-on moves; contraction precedes deleveraging).
#   https://stablecoins.llama.fi/stablecoins?includePrices=false
# circulating* are dicts keyed by pegType ("peggedUSD"); absent history
#   keys are common (newer assets) -> flows are None, not a crash.
# ============================================================================
def _flow(cur, prev):
    """Signed flow cur - prev; either side missing -> None."""
    c, p = _f(cur), _f(prev)
    if c is None or p is None:
        return None
    return c - p


def _parse_stablecoins(d):
    assets = d.get("peggedAssets")
    if assets is None:
        return None, "unexpected DeFiLlama stablecoins payload"
    rows = []
    for a in assets:
        circ = (a.get("circulating") or dict()).get("peggedUSD")
        if circ is None:
            continue
        rows.append(dict(
            symbol=a.get("symbol"),
            name=a.get("name"),
            peg=a.get("pegType"),
            mechanism=a.get("pegMechanism"),
            circulating=_f(circ),
            flow_1d=_flow(circ, (a.get("circulatingPrevDay") or dict())
                          .get("peggedUSD")),
            flow_1w=_flow(circ, (a.get("circulatingPrevWeek") or dict())
                          .get("peggedUSD")),
            flow_1m=_flow(circ, (a.get("circulatingPrevMonth") or dict())
                          .get("peggedUSD")),
        ))
    if not rows:
        return [], "no stablecoin rows parsed"
    rows.sort(key=lambda r: r["circulating"] or 0, reverse=True)
    return rows, None


def stablecoin_flows(limit=25):
    d, e = _clean_json("https://stablecoins.llama.fi/stablecoins"
                       "?includePrices=false", timeout=30)
    if e:
        return None, e
    rows, perr = _parse_stablecoins(d)
    if perr:
        return None, perr
    return rows[:int(limit)], None


# ============================================================================
# Deribit -- crypto vol surface. DVOL = 30d implied-vol index (the VIX of
#   BTC/ETH); get_book_summary_by_currency gives the full options chain
#   (mark in BTC/ETH terms, OI, volume). Instrument names look like
#   BTC-25SEP26-105000-C. The PERPETUAL row is filtered out here.
#   https://www.deribit.com/api/v2/public/get_volatility_index_data
#     ?currency=BTC&start_timestamp=...&end_timestamp=...&resolution=1D
#   https://www.deribit.com/api/v2/public/get_book_summary_by_currency
#     ?currency=BTC&kind=option
# ============================================================================
_INSTR_RE = _re.compile("^(?P<base>[A-Z0-9]+)-(?P<expiry>\\d{1,2}[A-Z]{3}\\d{2})-"
                        "(?P<strike>\\d+(?:\\.\\d+)?)-(?P<right>[CP])$")


def _parse_dvol(d):
    data = ((d.get("result") or dict()).get("data")) or []
    rows = []
    for bar in data:
        if not isinstance(bar, list) or len(bar) < 5:
            continue
        rows.append(dict(ts=int(bar[0]), open=_f(bar[1]), high=_f(bar[2]),
                         low=_f(bar[3]), close=_f(bar[4])))
    if not rows:
        return None, "no DVOL bars parsed"
    rows.sort(key=lambda r: r["ts"])
    return rows, None


def deribit_dvol(currency="BTC", days=30, resolution="1D"):
    end_ms = int(_time.time() * 1000)
    start_ms = end_ms - int(days) * 86400 * 1000
    d, e = _clean_json(
        "https://www.deribit.com/api/v2/public/get_volatility_index_data"
        "?currency=%s&start_timestamp=%d&end_timestamp=%d&resolution=%s"
        % (_urlparse_quote(currency), start_ms, end_ms,
           _urlparse_quote(resolution)))
    if e:
        return None, e
    return _parse_dvol(d)


def _parse_deribit_options(d, min_oi=1.0, right=None):
    src = d.get("result")
    if not isinstance(src, list):
        return None, "unexpected Deribit book summary payload"
    rows = []
    for o in src:
        m = _INSTR_RE.match(o.get("instrument_name") or "")
        if not m:
            continue
        oi = _f(o.get("open_interest"))
        if oi is None or oi < min_oi:
            continue
        if right and m.group("right") != right:
            continue
        rows.append(dict(
            instrument=o.get("instrument_name"),
            expiry=m.group("expiry"),
            strike=float(m.group("strike")),
            right=m.group("right"),
            mark=_f(o.get("mark_price")),
            bid=_f(o.get("bid_price")),
            ask=_f(o.get("ask_price")),
            volume=_f(o.get("volume")),
            open_interest=oi,
            underlying=_f(o.get("underlying_price")),
        ))
    rows.sort(key=lambda r: (r["expiry"], r["right"], r["strike"]))
    return rows, None


def deribit_options(currency="BTC", min_oi=1.0, right=None):
    d, e = _clean_json(
        "https://www.deribit.com/api/v2/public/get_book_summary_by_currency"
        "?currency=%s&kind=option" % _urlparse_quote(currency))
    if e:
        return None, e
    return _parse_deribit_options(d, min_oi=min_oi, right=right)


# ============================================================================
# Stocktwits symbol stream -- messages with OPTIONAL tagged sentiment
#   (Bullish/Bearish, set by the poster). entities.sentiment is absent when
#   untagged. sentiment_tally() aggregates a stream for screening.
#   https://api.stocktwits.com/api/2/streams/symbol/NVDA.json
# ============================================================================
def _parse_stocktwits(d):
    msgs = d.get("messages")
    if not isinstance(msgs, list):
        return None, "unexpected Stocktwits payload"
    rows = []
    for m in msgs:
        if not isinstance(m, dict):
            continue
        sent = (((m.get("entities") or dict()).get("sentiment") or dict())
                .get("basic"))
        rows.append(dict(
            id=m.get("id"),
            body=m.get("body"),
            created_at=m.get("created_at"),
            user=((m.get("user") or dict()).get("username")),
            sentiment=sent,
        ))
    if not rows:
        return None, "no Stocktwits messages parsed"
    return rows, None


def sentiment_tally(rows):
    """Aggregate a _parse_stocktwits rows list -> dict(n, bullish, bearish,
    unlabeled)."""
    n = len(rows)
    bull = sum(1 for r in rows if r.get("sentiment") == "Bullish")
    bear = sum(1 for r in rows if r.get("sentiment") == "Bearish")
    return dict(n=n, bullish=bull, bearish=bear, unlabeled=n - (bull + bear))


def stocktwits_stream(sym, _max=30):
    d, e = _clean_json(
        "https://api.stocktwits.com/api/2/streams/symbol/%s.json"
        % _urlparse_quote(sym.upper()), timeout=20)
    if e:
        return None, e
    return _parse_stocktwits(d)


# ============================================================================
# mempool.space -- Bitcoin fee market. Spiking fast/hour fees = on-chain
#   congestion/stress (flight-safety signal, exchange-run risk proxy).
#   https://mempool.space/api/v1/fees/recommended
# ============================================================================
def _parse_mempool_fees(d):
    keys = ("fastestFee", "halfHourFee", "hourFee", "economyFee", "minimumFee")
    if not all(k in d for k in keys):
        return None, "unexpected mempool payload"
    return dict(fastest_fee=_f(d.get("fastestFee")),
                half_hour_fee=_f(d.get("halfHourFee")),
                hour_fee=_f(d.get("hourFee")),
                economy_fee=_f(d.get("economyFee")),
                minimum_fee=_f(d.get("minimumFee"))), None


def mempool_fees():
    d, e = _clean_json("https://mempool.space/api/v1/fees/recommended")
    if e:
        return None, e
    return _parse_mempool_fees(d)


# ============================================================================
# NOAA National Hurricane Center -- active storms (energy/insurance risk).
#   https://www.nhc.noaa.gov/CurrentStorms.json
# intensity is knots, pressure hPa; both arrive as strings.
# ============================================================================
def _parse_nhc_storms(d):
    storms = d.get("activeStorms")
    if storms is None:
        return None, "unexpected NHC payload"
    rows = []
    for s in storms:
        rows.append(dict(
            id=s.get("id"),
            name=s.get("name"),
            classification=s.get("classification"),
            intensity_kt=_f(s.get("intensity")),
            pressure_hpa=_f(s.get("pressure")),
            lat=s.get("latitude"),
            lon=s.get("longitude"),
            bin=s.get("binNumber"),
        ))
    rows.sort(key=lambda r: r.get("intensity_kt") or 0, reverse=True)
    return rows, None


def nhc_storms():
    d, e = _clean_json("https://www.nhc.noaa.gov/CurrentStorms.json",
                       timeout=20)
    if e:
        return None, e
    return _parse_nhc_storms(d)


# ============================================================================
# Google Trends "Trending Now" RSS -- daily trending searches with traffic
#   volume. A retail-attention radar that complements the Wikipedia
#   pageviews feed in altdata4 (query-level, not article-level).
#   https://trends.google.com/trending/rss?geo=US
#   ht:approx_traffic like "500+", "20K+" -> traffic_n int.
# ============================================================================
_GT_NS = dict(ht="https://trends.google.com/trending/rss")


def _traffic_n(txt):
    if not txt:
        return None
    t = txt.strip().rstrip("+").upper().strip()
    mult = 1
    if t.endswith("K"):
        mult, t = 1000, t[:-1]
    elif t.endswith("M"):
        mult, t = 1000000, t[:-1]
    v = _f(t)
    return v * mult if v is not None else None


def _parse_gtrends(xml_txt):
    if not xml_txt or not xml_txt.strip():
        return [], None
    try:
        root = _ET.fromstring(xml_txt)
    except _ET.ParseError as e:
        return None, describe_err(e)
    rows = []
    for item in root.iter("item"):
        rows.append(dict(
            title=(item.findtext("title") or "").strip(),
            traffic_n=_traffic_n(item.findtext("ht:approx_traffic", None,
                                               _GT_NS)),
            news_title=(item.findtext("ht:news_item_title", None, _GT_NS)
                        or "").strip() or None,
            news_url=(item.findtext("ht:news_item_url", None, _GT_NS)
                      or "").strip() or None,
            pub_date=(item.findtext("pubDate") or "").strip(),
        ))
    rows.sort(key=lambda r: r["traffic_n"] or 0, reverse=True)
    return rows, None


def google_trends(geo="US", limit=20):
    txt, e = _clean_get("https://trends.google.com/trending/rss?geo=%s"
                        % _urlparse_quote(geo), timeout=20)
    if e:
        return None, e
    rows, perr = _parse_gtrends(txt)
    if perr:
        return None, perr
    return rows[:int(limit)], None


# ============================================================================
# Bitget USDT-FUTURES tickers -- ~200 perp pairs in ONE call with funding
#   rate, open interest (holdingAmount), mark/index price, 24h change.
#   Broadest keyless perp snapshot (Binance 451, Bybit 403 from this env).
#   https://api.bitget.com/api/v2/mix/market/tickers?productType=USDT-FUTURES
# code "00000" = ok. NOTE: change24h here is a FRACTION (-0.01385 = -1.4%).
# ============================================================================
def _parse_bitget_tickers(d):
    if str(d.get("code")) not in ("0", "00000"):
        return None, "Bitget code %s: %s" % (d.get("code"), d.get("msg"))
    rows = []
    for t in d.get("data") or []:
        if not isinstance(t, dict) or not t.get("symbol"):
            continue
        rows.append(dict(
            symbol=t.get("symbol"),
            last=_f(t.get("lastPr")),
            mark=_f(t.get("markPrice")),
            index=_f(t.get("indexPrice")),
            change_24h=_f(t.get("change24h")),
            high_24h=_f(t.get("high24h")),
            low_24h=_f(t.get("low24h")),
            base_volume=_f(t.get("baseVolume")),
            usdt_volume=_f(t.get("usdtVolume")),
            open_interest=_f(t.get("holdingAmount")),
            funding_rate=_f(t.get("fundingRate")),
            open_utc=_f(t.get("openUtc")),
        ))
    if not rows:
        return None, "no Bitget tickers parsed"
    return rows, None


def bitget_tickers(product_type="USDT-FUTURES"):
    d, e = _clean_json(
        "https://api.bitget.com/api/v2/mix/market/tickers?productType=%s"
        % _urlparse_quote(product_type), timeout=25)
    if e:
        return None, e
    return _parse_bitget_tickers(d)


# ============================================================================
# FINRA consolidatedShortInterest -- exchange-wide short interest with
#   days-to-cover, twice monthly. THE retail-accessible SI dataset (the
#   Nasdaq SI list in altdata2 covers NASDAQ-listed only).
#   POST https://api.finra.org/data/group/otcMarket/name/
#        consolidatedShortInterest
#        body: dict(limit=N, compareFilters=[dict(fieldName=settlementDate,
#                  fieldValue=YYYY-MM-DD, compareType=GREATER)])
#   GOTCHAS: the server speaks CSV only -- format=json in the URL is NOT
#   honored; without a settlementDate filter it streams a 2020 seed
#   snapshot from the oldest rows, so the filter is mandatory for current
#   data. Error responses are also CSV: "error,message" header.
# ============================================================================
_CSI_COLS = dict(symbol="symbolCode", name="issueName",
                 short_pos="currentShortPositionQuantity",
                 prev_short_pos="previousShortPositionQuantity",
                 avg_vol="averageDailyVolumeQuantity",
                 days_to_cover="daysToCoverQuantity",
                 chg_pct="changePercent",
                 settlement="settlementDate",
                 market="marketClassCode")


def _parse_finra_csi(csv_txt, limit=500):
    if not csv_txt or not csv_txt.strip():
        return [], "empty FINRA payload"
    rdr = _csv.DictReader(_io.StringIO(csv_txt))
    if not rdr.fieldnames:
        return [], "empty FINRA payload"
    if "error" in [f.strip(chr(34)).lower() for f in rdr.fieldnames]:
        first = next(rdr, dict())
        return None, "FINRA error: %s" % list(first.values())
    rows = []
    for r in rdr:
        sym = (r.get(_CSI_COLS["symbol"]) or "").strip()
        if not sym:
            continue
        rows.append(dict(
            symbol=sym,
            name=r.get(_CSI_COLS["name"]),
            short_pos=int(_f(r.get(_CSI_COLS["short_pos"])) or 0),
            prev_short_pos=int(_f(r.get(_CSI_COLS["prev_short_pos"])) or 0),
            avg_vol=int(_f(r.get(_CSI_COLS["avg_vol"])) or 0),
            days_to_cover=_f(r.get(_CSI_COLS["days_to_cover"])),
            chg_pct=_f(r.get(_CSI_COLS["chg_pct"])),
            settlement=r.get(_CSI_COLS["settlement"]),
            market=r.get(_CSI_COLS["market"]),
        ))
    if not rows:
        return None, "no FINRA CSI rows parsed"
    rows.sort(key=lambda r: (r["settlement"] or "",
                             r["days_to_cover"] or 0), reverse=True)
    return rows[:int(limit)], None


def finra_short_interest(limit=500, since=None, min_dtc=None):
    """Exchange-wide consolidated short interest, newest settlements first.
    since: YYYY-MM-DD floor on settlementDate (default 45d back -- the SI
    cycle is semi-monthly). min_dtc: keep rows with daysToCover >= this."""
    since = since or (_dt.date.today()
                      - _dt.timedelta(days=45)).isoformat()
    body = _json.dumps(dict(
        limit=int(limit),
        compareFilters=[dict(fieldName="settlementDate",
                             fieldValue=since,
                             compareType="GREATER")])).encode("utf-8")
    txt, e = _clean_post(
        "https://api.finra.org/data/group/otcMarket/name/"
        "consolidatedShortInterest", body=body,
        headers=dict([("Content-Type", "application/json")]), timeout=30)
    if e:
        return None, e
    rows, perr = _parse_finra_csi(txt, limit=limit)
    if perr:
        return None, perr
    if min_dtc is not None:
        rows = [r for r in rows if (r["days_to_cover"] or 0) >= min_dtc]
    return rows, None


# ============================================================================
# ECB Data Portal (SDMX 2.1 csvdata) -- institutional-grade eurozone data.
#   EXR = euro reference FX rates; FM/B.U2.EUR.4F.KR.MRR_FR.LEV = the
#   deposit-facility (MRR) policy rate. Complements Frankfurter (which is
#   ECB-derived anyway) with the full EXR universe + rates.
#   https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
#     ?startPeriod=2026-09-01&format=csvdata
# OBS_VALUE blank (with OBS_STATUS flag) = missing observation -> dropped.
# ============================================================================
def _parse_ecb_series(csv_txt):
    if not csv_txt or not csv_txt.strip():
        return [], "empty ECB payload"
    try:
        rdr = _csv.DictReader(_io.StringIO(csv_txt))
        rows = []
        for r in rdr:
            period = (r.get("TIME_PERIOD") or "").strip()
            v = _f(r.get("OBS_VALUE"))
            if period and v is not None:
                rows.append((period, v))
    except Exception as e:
        return None, describe_err(e)
    if not rows:
        return None, "no ECB observations parsed"
    rows.sort(key=lambda kv: kv[0])
    return rows, None


def ecb_series(key, start=None, end=None):
    """key like EXR/D.USD.EUR.SP00.A (daily USD/EUR) or
    FM/B.U2.EUR.4F.KR.MRR_FR.LEV (ECB deposit-facility rate)."""
    q = "startPeriod=%s" % (start or (_dt.date.today()
                                      - _dt.timedelta(days=30)).isoformat())
    if end:
        q += "&endPeriod=" + _urlparse_quote(end)
    txt, e = _clean_get(
        "https://data-api.ecb.europa.eu/service/data/%s?%s&format=csvdata"
        % (_urlparse_quote(key, safe="/"), q), timeout=30)
    if e:
        return None, e
    return _parse_ecb_series(txt)


# ============================================================================
# SINGLE ENTRY POINT -- run all altdata6 fetches in parallel.
# ============================================================================
def alt_data_sweep():
    """Run all altdata6 fetches in parallel. Returns dict of (name: (data, err))."""
    jobs = dict(
        cnbc_quotes=lambda: cnbc_quotes(
            ["NVDA", "AAPL", "600519.SS", "0700.HK", ".SPX", ".IXIC",
             "@GC.1", "@CL.1", "US2Y", "US10Y", "EUR=", "BTC="]),
        ff_calendar=lambda: ff_calendar(min_impact="High"),
        nasdaq_earnings=nasdaq_earnings,
        nasdaq_ipo=nasdaq_ipo,
        nasdaq_dividends=nasdaq_dividends,
        stablecoin_flows=lambda: stablecoin_flows(10),
        deribit_dvol=lambda: deribit_dvol("BTC", days=30),
        deribit_options=lambda: deribit_options("BTC", min_oi=50.0),
        stocktwits_nvda=lambda: stocktwits_stream("NVDA"),
        mempool_fees=mempool_fees,
        nhc_storms=nhc_storms,
        google_trends=lambda: google_trends("US", 10),
        bitget_tickers=bitget_tickers,
        finra_short_interest=lambda: finra_short_interest(limit=200,
                                                          min_dtc=5.0),
        ecb_usd=lambda: ecb_series("EXR/D.USD.EUR.SP00.A"),
        ecb_mrr=lambda: ecb_series("FM/B.U2.EUR.4F.KR.MRR_FR.LEV",
                                   start="2026-01-01"),
    )
    out = dict()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = dict()
        for name, fn in jobs.items():
            futs[pool.submit(fn)] = name
        for fut in futs:
            name = futs[fut]
            try:
                out[name] = fut.result(timeout=120)
            except Exception as e:
                out[name] = (None, describe_err(e))
    return out
