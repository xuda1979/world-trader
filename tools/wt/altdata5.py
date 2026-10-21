"""altdata5 -- new free data sources added 2026-09-08.

All sources here are FREE and need NO API key. Each fetcher returns
(data, err) consistent with the rest of the package.

Sources in this module (all verified reachable from this env on 2026-09-08;
everything goes through _clean_get, same flaky-proxy caveat as altdata3/4):

  - Frankfurter (ECB)               -> daily FX history + snapshot (the
                                       Yahoo/Stooq replacement for FX; ECB
                                       reference rates, ~40 currencies)
  - Kraken OHLC + ticker            -> crypto candle history (Binance is
                                       HTTP 451 from this env)
  - Coinbase Exchange candles       -> second crypto candle source (US view)
  - OKX candles + funding history   -> third OHLC source + funding-rate
                                       history (altdata3 only has snapshots)
  - Polymarket gamma                -> prediction-market odds with real
                                       liquidity (Manifold is thin)
  - TreasuryDirect TA_WS            -> auction calendar + bid-to-cover/price/
                                       yield results (fiscaldata auctions
                                       endpoint 404s from this env)
  - Google News RSS                 -> per-ticker news radar (headline count
                                       as attention proxy)
  - Reddit Atom feed                -> WSB top posts (retail sentiment)
  - Eurostat SDMX-JSON              -> EU HICP inflation (macro cross-check)
  - BLS public API v1 (keyless)     -> CPI etc. without a FRED/BLS key
  - World Bank indicators v2        -> long-horizon country macro
  - Nasdaq screener                 -> full US listing universe with sector
                                       + mcap caps (screening input)

Probed and REJECTED on 2026-09-08 (blocked from this env, do not re-probe
without VPN): GDELT 2.0 doc API (HTTP 429 on every attempt, >=5s spacing),
Philly Fed ADS CSV (403), Census EITS timeseries (404), iShares/SSGA ETF
holdings CSV (404 HTML), Binance klines (HTTP 451), Stooq (bot-check HTML).
GDELT may work from a different IP -- its published limit is 1 req/5s and we
backed off 6s x3 with no luck, so it is the first candidate to re-test.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, describe_err

import datetime as _dt
import json as _json
import re as _re
import time as _time
import urllib.parse as _urlparse
import xml.etree.ElementTree as _ET

_urlparse_quote = _urlparse.quote

# ---------------------------------------------------------------------------
# Resilient fetch helpers (same rationale as altdata3/4: this network has a
# flaky transparent proxy that intermittently serves a captive-portal page).
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
        return float(str(x).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None


def _date_of(ts):
    """ISO date prefix of a TreasuryDirect timestamp ("2026-09-08T...")."""
    return (ts or "")[:10]


# ============================================================================
# Frankfurter (ECB reference rates) -- daily FX history, ~40 currencies.
#   https://api.frankfurter.app/2026-08-24..2026-09-07?from=USD&to=CNY,EUR
#   https://api.frankfurter.app/latest?from=USD
# No key. Note: ECB publishes reference rates only on TARGET business days.
# ============================================================================
_FRANK_HIST = "https://api.frankfurter.app/%s..%s?from=USD&to=%s"
_FRANK_LATEST = "https://api.frankfurter.app/latest?from=USD&to=%s"


def _parse_frank_rates(d, ccy):
    """Frankfurter payload -> sorted [(date, rate)]. Empty rates -> error
    (caller asked for a range; silence means the request was wrong)."""
    rates = d.get("rates") if isinstance(d, dict) else None
    if not rates:
        return [], "no rates in Frankfurter payload"
    rows = []
    for day in sorted(rates):
        v = _f((rates[day] or dict()).get(ccy))
        if v is not None:
            rows.append((day, v))
    return rows, None


def fx_history(ccy="CNY", start=None, end=None, days=30):
    """Daily USD->ccy FX history (oldest first), default trailing window."""
    end = end or _dt.date.today().isoformat()
    start = start or (_dt.date.today()
                      - _dt.timedelta(days=int(days))).isoformat()
    d, e = _clean_json(_FRANK_HIST % (start, end, _urlparse_quote(ccy)))
    if e:
        return None, e
    return _parse_frank_rates(d, ccy)


def fx_snapshot(ccys="CNY,EUR,JPY,GBP,CHF,AUD,CAD,KRW,INR,BRL,MXN,TWD"):
    """Latest USD->cccy reference rates in one call (default: the majors
    plus the EM names this repo trades)."""
    d, e = _clean_json(_FRANK_LATEST % _urlparse_quote(ccys))
    if e:
        return None, e
    rates = (d.get("rates") if isinstance(d, dict) else None) or dict()
    out = dict(date=d.get("date"), base=d.get("base"), rates=rates)
    if not rates:
        return None, "no rates in Frankfurter payload"
    return out, None


# ============================================================================
# Kraken -- crypto OHLC history + ticker. Binance is 451 from this env, so
#   this is the primary crypto candle source.
#   https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60
#   https://api.kraken.com/0/public/Ticker?pair=XBTUSD
# ============================================================================
def _parse_kraken_ohlc(d):
    errs = d.get("error") or []
    if errs:
        return None, "; ".join(str(x) for x in errs)
    result = d.get("result") or dict()
    if not result:
        return None, "empty Kraken result"
    rows = []
    for _pair, candles in result.items():
        if not isinstance(candles, list):
            continue
        for c in candles:
            if len(c) < 8:
                continue
            rows.append(dict(ts=int(_f(c[0])), open=_f(c[1]), high=_f(c[2]),
                             low=_f(c[3]), close=_f(c[4]), vwap=_f(c[5]),
                             volume=_f(c[6]), count=int(_f(c[7]))))
    if not rows:
        return None, "no candles parsed"
    rows.sort(key=lambda r: r["ts"])
    return rows, None


def kraken_ohlc(pair="XBTUSD", interval=60):
    """interval in minutes: 1,5,15,30,60,240,1440. ~720 candles returned."""
    d, e = _clean_json("https://api.kraken.com/0/public/OHLC?pair=%s&interval=%d"
                       % (_urlparse_quote(pair), int(interval)))
    if e:
        return None, e
    return _parse_kraken_ohlc(d)


def kraken_ticker(pair="XBTUSD"):
    d, e = _clean_json("https://api.kraken.com/0/public/Ticker?pair=%s"
                       % _urlparse_quote(pair))
    if e:
        return None, e
    errs = d.get("error") or []
    if errs:
        return None, "; ".join(str(x) for x in errs)
    result = d.get("result") or dict()
    if not result:
        return None, "empty Kraken result"
    _pair, t = next(iter(result.items()))
    return dict(ask=_f((t.get("a") or [None])[0]), bid=_f((t.get("b") or [None])[0]),
                last=_f((t.get("c") or [None])[0]),
                vol_today=_f((t.get("v") or [None, None])[1]),
                low_today=_f((t.get("l") or [None, None])[1]),
                high_today=_f((t.get("h") or [None, None])[1]),
                open_today=_f((t.get("o") or [None])[0])), None


# ============================================================================
# Coinbase Exchange candles -- US crypto venue, newest-first payload.
#   https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400
# granularities: 60, 300, 900, 3600, 21600, 86400. Columns are
# [time, low, high, open, close, volume] -- note low BEFORE high.
# ============================================================================
def _parse_cb_candles(txt):
    try:
        raw = _json.loads(txt)
    except Exception as e:
        return None, describe_err(e)
    if not isinstance(raw, list):
        return None, "unexpected Coinbase candle payload"
    rows = []
    for c in raw:
        if len(c) < 6:
            continue
        rows.append(dict(ts=int(c[0]), low=_f(c[1]), high=_f(c[2]),
                         open=_f(c[3]), close=_f(c[4]), volume=_f(c[5])))
    if not rows:
        return None, "no candles parsed"
    rows.sort(key=lambda r: r["ts"])
    return rows, None


def coinbase_candles(product="BTC-USD", granularity=86400):
    txt, e = _clean_get(
        "https://api.exchange.coinbase.com/products/%s/candles?granularity=%d"
        % (_urlparse_quote(product), int(granularity)))
    if e:
        return None, e
    return _parse_cb_candles(txt)


# ============================================================================
# OKX -- candles + funding-rate HISTORY (altdata3's hyperliquid module only
#   has current funding; this gives the realized series).
#   .../market/candles?instId=BTC-USDT&bar=1D&limit=100
#   .../public/funding-rate-history?instId=BTC-USDT-SWAP&limit=100
# Both return newest-first; both are reversed here.
# ============================================================================
_OKX_BAR = dict(m1="1m", m5="5m", m15="15m", m30="30m", h1="1H", h4="4H",
                h8="8H", d1="1D")


def _parse_okx_candles(d):
    if str(d.get("code")) != "0":
        return None, "OKX code %s: %s" % (d.get("code"), d.get("msg"))
    rows = []
    for c in d.get("data") or []:
        if len(c) < 6:
            continue
        rows.append(dict(ts=int(_f(c[0])), open=_f(c[1]), high=_f(c[2]),
                         low=_f(c[3]), close=_f(c[4]), volume=_f(c[5])))
    if not rows:
        return None, "no candles parsed"
    rows.sort(key=lambda r: r["ts"])
    return rows, None


def okx_candles(inst="BTC-USDT", bar="1D", limit=100):
    d, e = _clean_json(
        "https://www.okx.com/api/v5/market/candles?instId=%s&bar=%s&limit=%d"
        % (_urlparse_quote(inst), _urlparse_quote(bar), int(limit)))
    if e:
        return None, e
    return _parse_okx_candles(d)


def _parse_okx_funding(d):
    if str(d.get("code")) != "0":
        return None, "OKX code %s: %s" % (d.get("code"), d.get("msg"))
    rows = []
    for c in d.get("data") or []:
        if isinstance(c, dict):
            # live funding-rate-history payload: dict rows
            row = dict(rate=_f(c.get("fundingRate")),
                       ts=int(_f(c.get("fundingTime"))),
                       inst=c.get("instId"))
        else:
            # positional rows (candles-style), kept for robustness
            if len(c) < 2:
                continue
            row = dict(rate=_f(c[0]), ts=int(_f(c[1])),
                       inst=c[2] if len(c) > 2 else None)
        if row["rate"] is None or row["ts"] is None:
            continue
        rows.append(row)
    if not rows:
        return None, "no funding rows parsed"
    rows.sort(key=lambda r: r["ts"])
    return rows, None


def okx_funding_history(inst="BTC-USDT-SWAP", limit=100):
    d, e = _clean_json(
        "https://www.okx.com/api/v5/public/funding-rate-history"
        "?instId=%s&limit=%d" % (_urlparse_quote(inst), int(limit)))
    if e:
        return None, e
    return _parse_okx_funding(d)


# ============================================================================
# Polymarket gamma API -- prediction-market odds with real liquidity.
#   https://gamma-api.polymarket.com/markets?limit=N&active=true&closed=false
#   &order=volume24hr&ascending=false
# outcomePrices/outcomes arrive as JSON-encoded STRINGS -> parse twice.
# ============================================================================
def _parse_pm_markets(raw_list):
    rows = []
    for m in raw_list or []:
        if not isinstance(m, dict):
            try:
                m = _json.loads(m)
            except Exception:
                continue
        def _sub(v):
            try:
                return _json.loads(v) if isinstance(v, str) else (v or [])
            except Exception:
                return []
        outcomes = _sub(m.get("outcomes"))
        prices = _sub(m.get("outcomePrices"))
        probs = dict()
        for name, px in zip(outcomes, prices):
            fv = _f(px)
            if name is not None and fv is not None:
                probs[str(name)] = fv
        bid, ask = _f(m.get("bestBid")), _f(m.get("bestAsk"))
        rows.append(dict(
            question=m.get("question"),
            slug=m.get("slug"),
            probs=probs,
            yes=probs.get("Yes"),
            best_bid=bid,
            best_ask=ask,
            spread=(ask - bid) if (bid is not None and ask is not None) else None,
            volume24hr=_f(m.get("volume24hr")),
            liquidity=_f(m.get("liquidityNum")),
            end_date=(m.get("endDate") or "")[:10] or None,
            closed=bool(m.get("closed")),
        ))
    return rows, None


def polymarket_markets(limit=10, order="volume24hr"):
    """Top active markets by 24h volume (default) -- macro/politics odds
    with real money on them. Set order=endDate for soonest-resolving."""
    d, e = _clean_json(
        "https://gamma-api.polymarket.com/markets?limit=%d&active=true"
        "&closed=false&order=%s&ascending=false" % (int(limit), _urlparse_quote(order)))
    if e:
        return None, e
    if not isinstance(d, list):
        return None, "unexpected Polymarket payload"
    return _parse_pm_markets(d)


# ============================================================================
# TreasuryDirect TA_WS -- auction calendar AND results (bid-to-cover, price,
#   high yield). fiscaldata auctions-query 404s from this env; this works.
#   https://www.treasurydirect.gov/TA_WS/securities/search?startDate=YYYYMMDD
#   &endDate=YYYYMMDD&type=Bill|Note|Bond|TIPS|FRN|CofB&format=json
# Result fields are "" until the auction settles; parse fail-soft to None.
# ============================================================================
def _parse_td_securities(recs):
    rows = []
    for r in recs or []:
        rows.append(dict(
            cusip=r.get("cusip"),
            security_type=r.get("securityType"),
            term=r.get("securityTerm"),
            auction_date=_date_of(r.get("auctionDate")),
            issue_date=_date_of(r.get("issueDate")),
            maturity_date=_date_of(r.get("maturityDate")),
            offering_mm=round(_f(r.get("offeringAmount")) / 1e6)
            if _f(r.get("offeringAmount")) else None,
            bid_to_cover=_f(r.get("bidToCoverRatio")),
            price_per_100=_f(r.get("pricePer100")),
            high_yield=_f(r.get("highInvestmentRate")),
            interest_rate=_f(r.get("interestRate")),
        ))
    rows.sort(key=lambda x: x.get("auction_date") or "", reverse=True)
    return rows, None


def treasury_auctions(days_ahead=14, days_back=21, sec_type=None, limit=50):
    """Auction calendar + settled results around today. sec_type in
    Bill/Note/Bond/TIPS/FRN/CofB (None = all)."""
    start = _dt.date.today() - _dt.timedelta(days=int(days_back))
    end = _dt.date.today() + _dt.timedelta(days=int(days_ahead))
    q = "startDate=%s&endDate=%s&format=json" % (start.strftime("%Y%m%d"),
                                                 end.strftime("%Y%m%d"))
    if sec_type:
        q += "&type=" + _urlparse_quote(sec_type)
    d, e = _clean_json("https://www.treasurydirect.gov/TA_WS/securities/search?"
                       + q)
    if e:
        return None, e
    if not isinstance(d, list):
        return None, "unexpected TreasuryDirect payload"
    rows, _ = _parse_td_securities(d)
    return rows[:int(limit)], None


# ============================================================================
# Google News RSS -- per-ticker/topic news radar. Headline volume is an
#   attention proxy; publishers tag the wire.
#   https://news.google.com/rss/search?q=Tesla&hl=en-US&gl=US&ceid=US:en
# Titles arrive as "headline - Publisher" -> split on the last " - ".
# ============================================================================
def _parse_rss_items(xml_txt):
    if not xml_txt or not xml_txt.strip():
        return [], None
    try:
        root = _ET.fromstring(xml_txt)
    except _ET.ParseError as e:
        return None, describe_err(e)
    rows = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        pub = item.findtext("source")
        pub = pub.strip() if pub else ""
        head = title
        if pub and title.endswith(" - " + pub):
            head = title[: -(len(pub) + 3)].strip()
        rows.append(dict(headline=head, publisher=pub or None,
                         link=(item.findtext("link") or "").strip(),
                         pub_date=(item.findtext("pubDate") or "").strip()))
    return rows, None


def google_news(query, limit=15):
    q = _urlparse.quote(query)
    txt, e = _clean_get(
        "https://news.google.com/rss/search?q=%s&hl=en-US&gl=US&ceid=US:en"
        % q, timeout=20)
    if e:
        return None, e
    rows, perr = _parse_rss_items(txt)
    if perr:
        return None, perr
    return rows[:int(limit)], None


# ============================================================================
# Reddit Atom feed -- r/wallstreetbets top posts (retail-sentiment radar).
#   https://www.reddit.com/r/wallstreetbets/top/.rss?t=day
# ============================================================================
def _parse_atom_entries(xml_txt):
    if not xml_txt or not xml_txt.strip():
        return [], None
    try:
        root = _ET.fromstring(xml_txt)
    except _ET.ParseError as e:
        return None, describe_err(e)
    ns = dict(atom="http://www.w3.org/2005/Atom")
    rows = []
    for entry in root.findall("atom:entry", ns):
        link_el = entry.find("atom:link", ns)
        author_el = entry.find("atom:author/atom:name", ns)
        cat_el = entry.find("atom:category", ns)
        rows.append(dict(
            title=(entry.findtext("atom:title", "", ns) or "").strip(),
            link=(link_el.get("href") if link_el is not None else "") or "",
            updated=(entry.findtext("atom:updated", "", ns) or "").strip(),
            author=(author_el.text or "").strip() if author_el is not None else None,
            flair=(cat_el.get("term") if cat_el is not None else None),
        ))
    return rows, None


def reddit_top(sub="wallstreetbets", t="day", limit=15):
    """t in hour/day/week/month/year/all."""
    txt, e = _clean_get(
        "https://www.reddit.com/r/%s/top/.rss?t=%s" % (_urlparse_quote(sub),
                                                       _urlparse_quote(t)),
        timeout=20)
    if e:
        return None, e
    rows, perr = _parse_atom_entries(txt)
    if perr:
        return None, perr
    return rows[:int(limit)], None


# ============================================================================
# Eurostat SDMX-JSON -- EU macro without scraping (HICP inflation etc.).
#   .../1.0/data/prc_hicp_manr?format=JSON&lang=EN&geo=EA20&unit=RCH_A
#   &coicop=CP00&sinceTimePeriod=2025-01
# Response is a flat cube: value{"flat-index": v}, dimension.time.category
# .index maps period -> index along the LAST axis. Monthly, lags ~2-4 weeks
# after reference month (Eurostat flash timing).
# ============================================================================
def _cube_to_rows(d):
    """Eurostat SDMX-JSON cube -> sorted [(period, value)] along the time
    axis. Empty cube (no values) -> error, since a silent [] is how a bad
    filter (e.g. wrong geo code) presents."""
    values = d.get("value") or dict()
    idx = ((((d.get("dimension") or dict()).get("time") or dict())
            .get("category") or dict()).get("index")) or dict()
    if not values or not idx:
        return [], "no data in Eurostat cube"
    periods = [p for p, _ in sorted(idx.items(), key=lambda kv: kv[1])]
    rows = []
    for pos, period in enumerate(periods):
        v = values.get(str(pos))
        if v is not None:
            rows.append((period, v))
    return rows, None


def eurostat_hicp(geo="EA20", coicop="CP00", unit="RCH_A", since="2025-01"):
    """EU HICP annual inflation rate (unit RCH_A = annual rate of change),
    headline (CP00) for the euro area by default."""
    d, e = _clean_json(
        "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
        "/prc_hicp_manr?format=JSON&lang=EN&geo=%s&coicop=%s&unit=%s"
        "&sinceTimePeriod=%s" % (_urlparse_quote(geo), _urlparse_quote(coicop),
                                 _urlparse_quote(unit), _urlparse_quote(since)))
    if e:
        return None, e
    rows, perr = _cube_to_rows(d)
    if perr:
        return None, perr
    return rows, None


# ============================================================================
# BLS public API v1 (GET, keyless) -- CPI/PPI/jobs series without a key.
#   https://api.bls.gov/publicAPI/v1/timeseries/data/{seriesId}
# Keyless GET returns the 3 most recent years. status REQUEST_FAILED ->
# error carrying the server's message list.
# ============================================================================
_BLS_PERIOD = _re.compile(r"^M(\d{2})$")


def _bls_series_rows(d):
    status = d.get("status") or ""
    msgs = "; ".join(str(m) for m in (d.get("message") or []))
    if status != "REQUEST_SUCCEEDED":
        return None, "BLS %s: %s" % (status or "no status", msgs or "unknown")
    rows = []
    for s in ((d.get("Results") or dict()).get("series")) or []:
        sid = s.get("seriesID")
        for o in s.get("data") or []:
            period = o.get("period") or ""
            if period == "M13":      # annual average -> skip for monthly work
                continue
            m = _BLS_PERIOD.match(period)
            ym = (o.get("year") + "-" + m.group(1)) if m else (o.get("year") or "")
            v = _f(o.get("value"))
            if v is None:
                continue
            rows.append(dict(series=sid, ym=ym, value=v,
                             latest=o.get("latest") == "true"))
    if not rows:
        return None, "no BLS observations parsed"
    rows.sort(key=lambda r: (r["ym"], r["series"]), reverse=True)
    return rows, None


def bls_series(*series_ids):
    """One or more BLS series ids, e.g. bls_series("CUSR0000SA0") for CPI-U
    SA, "CUUR0000SA0" for NSA, "WPSFD49207" for PPI commodities."""
    ids = [s.strip() for s in series_ids if s and s.strip()]
    if not ids:
        return None, "no series ids given"
    if len(ids) == 1:
        url = "https://api.bls.gov/publicAPI/v1/timeseries/data/" + _urlparse_quote(ids[0])
    else:
        url = ("https://api.bls.gov/publicAPI/v1/timeseries/data/"
               + ",".join(_urlparse_quote(i) for i in ids))
    d, e = _clean_json(url, timeout=25)
    if e:
        return None, e
    return _bls_series_rows(d)


# ============================================================================
# World Bank indicators v2 -- long-horizon country macro (GDP growth etc.).
#   https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.KD.ZG
#   ?format=json&date=2015:2026
# Payload is [metadata, rows]; error payloads are a single dict with
# "message". Null values (no observation for that year) are skipped.
# ============================================================================
def _parse_wb(d):
    if not isinstance(d, list) or len(d) < 2:
        if isinstance(d, dict) and d.get("message"):
            msgs = "; ".join(str(m.get("value") or m.get("id") or m)
                             for m in d["message"])
            return None, "World Bank: %s" % msgs
        return None, "unexpected World Bank payload"
    rows = []
    for r in d[1] or []:
        v = r.get("value")
        if v is None:
            continue
        rows.append((str(r.get("date")), _f(v)))
    rows.sort(key=lambda kv: kv[0], reverse=True)
    return rows, None


def worldbank_indicator(indicator, country="USA", date_from=2010):
    d, e = _clean_json(
        "https://api.worldbank.org/v2/country/%s/indicator/%s"
        "?format=json&date=%d:2026&per_page=200"
        % (_urlparse_quote(country), _urlparse_quote(indicator),
           int(date_from)))
    if e:
        return None, e
    return _parse_wb(d)


# ============================================================================
# Nasdaq screener -- full US listing universe with last sale, mcap, sector.
#   https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=...
# Caps at limit=7500 for everything. Good for building universes/filters
# (e.g. mcap floors) without paid screeners.
# ============================================================================
def _parse_nasdaq_rows(d):
    table = ((d.get("data") or dict()).get("table")) or dict()
    rows = []
    for r in table.get("rows") or []:
        sym = (r.get("symbol") or "").strip()
        if not sym:
            continue
        rows.append(dict(
            symbol=sym,
            name=r.get("name"),
            last_sale=_f((r.get("lastsale") or "").replace("$", "")),
            pct_change=_f((r.get("pctchange") or "").replace("%", "")),
            market_cap=r.get("marketCap"),
            country=r.get("country"),
            sector=r.get("sector"),
            industry=r.get("industry"),
        ))
    if not rows:
        return None, "no Nasdaq screener rows parsed"
    return rows, None


def nasdaq_universe(exchange="nasdaq", limit=7500):
    """exchange: nasdaq | nyse | amex | all."""
    d, e = _clean_json(
        "https://api.nasdaq.com/api/screener/stocks?tableonly=true"
        "&exchange=%s&limit=%d&download=false" % (_urlparse_quote(exchange),
                                                  int(limit)),
        timeout=30)
    if e:
        return None, e
    return _parse_nasdaq_rows(d)


# ============================================================================
# SINGLE ENTRY POINT -- run all keyless fetches in parallel.
# ============================================================================
def alt_data_sweep():
    """Run all altdata5 fetches in parallel. Returns dict of (name: (data, err))."""
    jobs = dict(
        fx_snapshot=fx_snapshot,
        kraken_ohlc_daily=lambda: kraken_ohlc("XBTUSD", interval=1440),
        coinbase_candles=lambda: coinbase_candles("BTC-USD", 86400),
        okx_candles=lambda: okx_candles("BTC-USDT", "1D", 30),
        okx_funding=lambda: okx_funding_history("BTC-USDT-SWAP", 30),
        polymarket_markets=polymarket_markets,
        treasury_auctions=lambda: treasury_auctions(sec_type="Bill"),
        google_news_nvda=lambda: google_news("NVIDIA"),
        reddit_wsb=lambda: reddit_top("wallstreetbets", "day"),
        eurostat_hicp=eurostat_hicp,
        bls_cpi=lambda: bls_series("CUSR0000SA0"),
        worldbank_gdp=lambda: worldbank_indicator("NY.GDP.MKTP.KD.ZG"),
        nasdaq_universe=lambda: nasdaq_universe("nasdaq", 100),
    )
    out = dict()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = dict()
        for name, fn in jobs.items():
            futs[pool.submit(fn)] = name
        for fut in futs:
            name = futs[fut]
            try:
                out[name] = fut.result(timeout=90)
            except Exception as e:
                out[name] = (None, describe_err(e))
    return out
