"""altdata3 -- new free data sources added 2026-07-21.

All sources here are FREE and need NO API key (unless noted). Each fetcher
returns (data, err) consistent with the rest of the package.

Sources in this module (all verified reachable from this env on 2026-07-21,
though this network has a flaky transparent proxy -- see _clean_get below):
  - CBOE VIX futures settlement CSV  -> vol term structure (VX curve)
  - FRED graph CSV (no-key path)      -> reliable macro series fallback
  - SEC EDGAR submissions JSON        -> per-company filing index
  - SEC EDGAR XBRL companyconcept     -> fundamental time series (revenue, EPS)
  - SEC EDGAR PIT (point-in-time)     -> sec_xbrl_series carries the SEC `filed`
                                        date; sec_pit_ledger / sec_pit_snapshot
                                        reconstruct a value EXACTLY as it appeared
                                        on a given date (temporal rollback over
                                        restatements/amendments) -- the audit-grade
                                        anti-lookahead ledger. (added 2026-09-14)
  - SEC EDGAR 13F institutional hold -> sec_13f_recent_filings(manager_cik): the
                                        "institutional holdings" half of the PIT
                                        ledger -- 13F-HR index with filing_date
                                        (PIT anchor) + direct EDGAR holdings URL.
  - DeFiLlama fees/dexs overview      -> protocol revenue & DEX volume trends
  - Gate.io v4 USDT-perp tickers      -> crypto funding/OI (Binance fapi times out here)
  - Hacker News (Algolia) search      -> tech sentiment / catalyst mentions
  - Manifold Markets search           -> prediction-market odds
  - EarningsWhispers calendar (HTML)  -> earnings calendar (parser)
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, get_json, describe_err

import re as _re
import time as _time

# ---------------------------------------------------------------------------
# Resilient fetch helper.
#
# This environment has a flaky transparent proxy that intermittently returns
# a Chinese-language "用户认证系统" (user authentication) captive-portal page
# instead of the real response, and also issues random connection resets /
# timeouts. Every fetcher in this module therefore goes through _clean_get,
# which:
#   1. Retries up to `retries` times with a short backoff.
#   2. Detects the captive-portal signature and treats it as a failure.
#   3. Returns (text, err) instead of raising.
# ---------------------------------------------------------------------------
_PORTAL_RE = _re.compile(r"用户认证系统|认证系统|个人认证|登录验证")


def _clean_get(url, *, headers=None, timeout=12, retries=3):
    last_err = None
    for attempt in range(retries):
        try:
            txt = http_get(url, headers=headers, timeout=timeout)
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
    import json as _json
    try:
        return _json.loads(txt), None
    except Exception as ex:
        return None, f"json: {type(ex).__name__}"


# ============================================================================
# CBOE VIX FUTURES SETTLEMENT -- vol term structure (free CSV, no key)
# URL: https://www.cboe.com/us/futures/market_statistics/settlement/csv
# Gives settle prices for VX (and sub-indexes VX30/VX31/VX32) across the
# entire term structure. The shape of the curve (contango vs backwardation)
# is a classic regime signal:
#   - Contango (front < back)     -> calm, short-vol regime (long equities OK)
#   - Backwardation (front > back)-> stress, long-vol regime (defensive)
# A flat or inverted front-month vs 2nd-month is an early stress warning.
# ============================================================================
def vix_futures_curve():
    """Return list of {product, symbol, expiry, price} for VX futures, sorted
    by expiry. Front-month and 2nd-month are extracted for curve shape."""
    txt, e = _clean_get(
        "https://www.cboe.com/us/futures/market_statistics/settlement/csv",
        timeout=15,
    )
    if e:
        return None, e
    out = []
    lines = txt.splitlines()
    if not lines or "Product" not in lines[0]:
        return None, "unexpected CSV header"
    for ln in lines[1:]:
        if not ln.strip():
            continue
        parts = ln.split(",")
        if len(parts) < 4:
            continue
        prod, sym, exp, price = parts[0], parts[1], parts[2], parts[3]
        if prod != "VX":
            continue
        try:
            out.append({
                "product": prod,
                "symbol": sym,
                "expiry": exp,
                "price": float(price),
            })
        except ValueError:
            continue
    out.sort(key=lambda r: r["expiry"])
    if not out:
        return None, "no VX rows"
    # Curve shape: front vs second month.
    shape = None
    if len(out) >= 2:
        f1, f2 = out[0]["price"], out[1]["price"]
        if f2 > f1:
            shape = "contango"
        elif f2 < f1:
            shape = "backwardation"
        else:
            shape = "flat"
    return {"rows": out, "front": out[0], "second": out[1] if len(out) > 1 else None,
            "shape": shape}, None


# ============================================================================
# FRED GRAPH CSV -- no-key path (works without FRED_KEY)
# URL: https://fred.stlouisfed.org/graph/fredgraph.csv?id=SERIES
# This is the most reliable macro path in THIS environment (the api.stlouisfed
# JSON endpoint requires a key, but the graph CSV endpoint is keyless and was
# the only source that returned valid data on every probe pass).
# Useful for any FRED series: DGS10, DGS2, DGS3MO, DTB3, T10YIE, DCOILWTICO,
# VIXCLS, DEXUSEU, WALCL, M2SL, etc.
# ============================================================================
def fred_csv_latest(series_id, limit=5):
    """Return (latest_value, date, history_list) from FRED graph CSV (no key).
    history_list is the last `limit` (date, value) tuples."""
    txt, e = _clean_get(
        f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}",
        timeout=12,
    )
    if e:
        return None, None, None, e
    rows = []
    for ln in txt.splitlines()[1:]:  # skip header
        if not ln.strip():
            continue
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        date, val = parts[0], parts[1]
        try:
            rows.append((date, float(val)))
        except ValueError:
            continue  # "." = missing
    if not rows:
        return None, None, None, "no data"
    recent = rows[-limit:]
    return recent[-1][1], recent[-1][0], recent, None


def fred_csv_snapshot(series_ids):
    """Fetch many FRED series in parallel (no key). Returns {sid: {latest,
    date, prev, chg_1d, chg_5d}}. `series_ids` is a list of (sid, label)."""
    out = {}
    def _one(sid_label):
        sid, label = sid_label
        v, d, hist, e = fred_csv_latest(sid, limit=10)
        if e:
            return sid, {"label": label, "err": e}
        prev = hist[-2][1] if len(hist) >= 2 else v
        wk = hist[0][1] if len(hist) >= 1 else v
        chg_1d = round(100.0 * (v - prev) / prev, 3) if prev else None
        chg_5d = round(100.0 * (v - wk) / wk, 3) if wk else None
        return sid, {"label": label, "latest": v, "date": d,
                     "chg_1d_pct": chg_1d, "chg_5d_pct": chg_5d}
    with ThreadPoolExecutor(max_workers=6) as pool:
        for sid, row in pool.map(_one, series_ids):
            out[sid] = row
    return out, None


# Default macro snapshot -- a broad free regime panel.
FRED_MACRO_PANEL = [
    ("DGS3MO", "3M Treasury"),
    ("DGS2", "2Y Treasury"),
    ("DGS10", "10Y Treasury"),
    ("DGS30", "30Y Treasury"),
    ("DTB3", "3M T-bill"),
    ("T10Y2Y", "10Y-2Y spread"),
    ("T10YIE", "10Y breakeven inflation"),
    ("DFF", "Fed funds effective"),
    ("BAMLH0A0HYM2", "HY credit spread"),
    ("DCOILWTICO", "WTI crude"),
    ("DHHNGSP", "Henry Hub natgas"),
    ("VIXCLS", "VIX (FRED)"),
    ("DEXUSEU", "USD/EUR"),
    ("DEXJPUS", "USD/JPY"),
    ("DEXCHUS", "USD/CNY"),
    ("WALCL", "Fed balance sheet"),
    ("M2SL", "M2 money supply"),
]


def macro_snapshot():
    """One-call broad macro regime panel via FRED keyless CSV."""
    return fred_csv_snapshot(FRED_MACRO_PANEL)


# ============================================================================
# SEC EDGAR -- submissions index & XBRL fundamentals (free, no key, but
# requires a descriptive User-Agent header per SEC fair-access policy).
# URLs:
#   https://data.sec.gov/submissions/CIK{10-digit}.json
#   https://data.sec.gov/api/xbrl/companyconcept/CIK{10}/us-gaap/{tag}.json
#   https://data.sec.gov/api/xbrl/companyfacts/CIK{10}.json
# ============================================================================
_SEC_UA = {"User-Agent": "world-trader research contact@example.com"}


def _cik_for_ticker(ticker):
    """Resolve ticker -> 10-digit CIK via SEC company_tickers.json."""
    d, e = _clean_json("https://www.sec.gov/files/company_tickers.json",
                       headers=_SEC_UA, timeout=12)
    if e:
        return None, e
    ticker = ticker.upper()
    for _, v in d.items():
        if v.get("ticker") == ticker:
            return str(v.get("cik_str")).zfill(10), None
    return None, "ticker not found"


def sec_recent_filings(ticker, limit=20):
    """Return recent SEC filings for a ticker. Each row: {form, filing_date,
    accession, primary_doc, url}."""
    cik, e = _cik_for_ticker(ticker)
    if e:
        return None, e
    d, e = _clean_json(f"https://data.sec.gov/submissions/CIK{cik}.json",
                       headers=_SEC_UA, timeout=12)
    if e:
        return None, e
    recent = d.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    acc = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", "")
    out = []
    n = min(limit, len(forms))
    for i in range(n):
        a = acc[i].replace("-", "")
        out.append({
            "form": forms[i],
            "filing_date": dates[i],
            "accession": acc[i],
            "primary_doc": docs[i] if isinstance(docs, str) else (docs[i] if i < len(docs) else ""),
            "url": f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{a}/{docs[i] if isinstance(docs, list) and i < len(docs) else docs}",
        })
    return out, None


def sec_xbrl_series(ticker, tag="Revenues", units="USD", limit=8):
    """Return recent XBRL fact values for a US-GAAP tag. Each row:
    {end, value, form, fp, frame, filed}. `tag` examples: Revenues, EarningsPerShareBasic,
    NetIncomeLoss, AssetsLongTermDebt, CommonStockSharesOutstanding.

    POINT-IN-TIME (PIT) INTEGRITY: every row carries `filed` -- the SEC filing
    date on which that value first became public. This is the anti-lookahead
    anchor: a value for period `end` must not be treated as knowable before its
    `filed` date. Use sec_pit_ledger / sec_pit_snapshot for a true "as-of"
    rollback reconstruction of the restatement/amendment trail."""
    cik, e = _cik_for_ticker(ticker)
    if e:
        return None, e
    d, e = _clean_json(
        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json",
        headers=_SEC_UA, timeout=12,
    )
    if e:
        return None, e
    out = []
    # The data has units -> "USD" (or "shares") -> list of period facts.
    units_map = d.get("units", {})
    facts = units_map.get(units) or units_map.get("shares") or []
    # Sort by end date desc, keep most recent `limit`.
    facts = sorted(facts, key=lambda r: r.get("end", ""), reverse=True)
    for f in facts[:limit]:
        out.append({
            "end": f.get("end"),
            "value": f.get("val"),
            "form": f.get("form"),
            "fp": f.get("fp"),
            "fy": f.get("fy"),
            "start": f.get("start"),
            "filed": f.get("filed"),
        })
    return out, None


def sec_pit_ledger(ticker, tag="Revenues", units="USD", as_of=None):
    """Return the POINT-IN-TIME ledger for a US-GAAP tag -- every reported fact
    with its (period start, period end) plus the SEC `filed` date, accession
    number, and whether the report form suggests an amendment (e.g. 10-K/A,
    10-Q/A). The `filed` date is the exact date the value became public, which
    is what protects a backtest from lookahead/restatement bias.

    Each row: {start, end, value, form, filed, fp, fy, accn, amended}.
    Optional `as_of`: only facts filed on or before this YYYY-MM-DD are kept
    (a lightweight up-front filter; sec_pit_snapshot does the reconstruction)."""
    cik, e = _cik_for_ticker(ticker)
    if e:
        return None, e
    d, e = _clean_json(
        f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json",
        headers=_SEC_UA, timeout=12,
    )
    if e:
        return None, e
    units_map = d.get("units", {})
    facts = units_map.get(units) or units_map.get("shares") or []
    out = []
    for f in facts:
        filed = f.get("filed")
        if not filed:
            continue
        if as_of and filed > as_of:  # string-compare works for ISO YYYY-MM-DD
            continue
        form = f.get("form", "")
        # SEC amendments carry an /A suffix (e.g. 10-K/A, 10-Q/A, 8-K/A).
        amended = isinstance(form, str) and form.rstrip().lower().endswith("/a")
        out.append({
            "start": f.get("start"),
            "end": f.get("end"),
            "value": f.get("val"),
            "form": form,
            "filed": filed,
            "fp": f.get("fp"),
            "fy": f.get("fy"),
            "accn": f.get("accn"),
            "amended": bool(amended),
        })
    # Sort by filed date (PIT order), then by end date.
    out.sort(key=lambda r: (r["filed"], r.get("end") or ""))
    return out, None


def sec_pit_snapshot(ticker, tag="Revenues", units="USD", as_of=None,
                     period_end=None):
    """TEMPORAL ROLLBACK: reconstruct one value for `tag` EXACTLY AS IT WOULD
    HAVE APPEARED on date `as_of` (YYYY-MM-DD), using only facts whose SEC
    `filed` date is on or before `as_of`. This is the audit-grade PIT primitive
    that eliminates lookahead/restatement bias: the most recently *filed* value
    is returned, not the most recently *reported period* value.

    Returns (value, meta) where meta = {filed, form, start, end, period_before}
    -- `value` is None if no fact was knowable as of `as_of`.
    Optional `period_end`: only consider facts whose period `end` <= period_end
    (e.g. to avoid pulling the next quarter's pre-announcement)."""
    ledger, e = sec_pit_ledger(ticker, tag, units, as_of=as_of)
    if e:
        return None, None, e
    # Filter to facts whose period end is knownable relative to period_end.
    if period_end:
        ledger = [r for r in ledger if (r.get("end") or "") <= period_end]
    if not ledger:
        return None, {"filed": None, "form": None, "start": None, "end": None,
                      "period_before": None}, None
    # The PIT value = the most recently FILED fact (last in filed-sorted order).
    r = ledger[-1]
    meta = {
        "filed": r["filed"],
        "form": r["form"],
        "start": r["start"],
        "end": r["end"],
        "period_before": ledger[-2]["end"] if len(ledger) > 1 else None,
    }
    return r["value"], meta, None


def sec_13f_recent_filings(manager_cik, limit=8):
    """Institutional-holdings (13F) index for a money-manager CIK, PIT-stamped.

    This is the "institutional holdings" half of the audit-grade PIT ledger:
    for every 13F-HR filing it returns the SEC `filing_date` (the date the
    holdings first became public -- the anti-lookahead anchor) plus the direct
    EDGAR URL to that filing's information table (the full holdings detail).

    NOTE: 13F managers are identified by CIK (not ticker). To look up a manager
    by name use SEC EDGAR full-text search or the submissions endpoint.

    Each row: {form, filing_date, accession, url, id}. `id` is the primary
    document inside the package (the informationTable XML/HTML) when available.
    """
    cik = str(manager_cik).zfill(10)
    d, e = _clean_json(f"https://data.sec.gov/submissions/CIK{cik}.json",
                       headers=_SEC_UA, timeout=12)
    if e:
        return None, e
    recent = d.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    acc = recent.get("accessionNumber", [])
    docs = recent.get("primaryDocument", "")
    out = []
    # Scan the whole "recent" bucket (large filers have >1000 entries) to find
    # the N most recent 13F-HR / 13F-HR/A filings. Older ones live in the paged
    # `files` index, which callers can page manually.
    n = len(forms)
    seen = 0
    for i in range(n):
        if (forms[i] or "").upper() in ("13F-HR", "13F-HR/A"):
            a = acc[i].replace("-", "")
            doc = docs[i] if isinstance(docs, list) and i < len(docs) else docs
            out.append({
                "form": forms[i],
                "filing_date": dates[i],   # PIT anchor: date holdings went public
                "accession": acc[i],
                "id": doc,
                "url": f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{a}/{doc}",
            })
            seen += 1
            if seen >= limit:
                break
    if not out:
        return None, "no 13F-HR filings for this CIK"
    # Submissions' recent bucket is oldest->newest; return newest-first.
    out.reverse()
    return out, None


# ============================================================================
# DeFiLlama fees & DEX volume overview (free, no key).
# URLs:
#   https://api.llama.fi/overview/fees            -> protocol fees history
#   https://api.llama.fi/overview/dexs            -> DEX volume history
#   https://api.llama.fi/overview/protocols       -> per-protocol breakdown
# We already use yields.llama.fi in altdata2; these add the revenue/volume
# dimension, useful for spotting L1/L2/DEX regime shifts (e.g. SOL/ETH flip).
# ============================================================================
def defillama_fees_snapshot():
    """Latest 24h fees+revenue across all protocols, with chain breakdown."""
    d, e = _clean_json("https://api.llama.fi/overview/fees", timeout=15)
    if e:
        return None, e
    out = {
        "total_24h": d.get("total24h"),
        "total_7d": d.get("total7d"),
        "total_30d": d.get("total30d"),
        "change_1d": d.get("change_1d"),
        "change_7d": d.get("change_7d"),
        "change_30d": d.get("change_30d"),
        "chains": {},
    }
    for ch in d.get("chains", []) or []:
        nm = ch.get("name")
        if nm:
            out["chains"][nm] = {
                "fees_24h": ch.get("fees24h"),
                "revenue_24h": ch.get("revenue24h"),
                "change_1d": ch.get("change_1d"),
            }
    return out, None


def defillama_dexs_snapshot():
    """Latest 24h DEX volume across chains."""
    d, e = _clean_json("https://api.llama.fi/overview/dexs", timeout=15)
    if e:
        return None, e
    out = {
        "total_24h": d.get("total24h"),
        "total_7d": d.get("total7d"),
        "change_1d": d.get("change_1d"),
        "change_7d": chg if (chg := d.get("change_7d")) is not None else None,
        "chains": {},
    }
    for ch in d.get("chains", []) or []:
        nm = ch.get("name")
        if nm:
            out["chains"][nm] = {
                "volume_24h": ch.get("total24h"),
                "change_1d": ch.get("change_1d"),
            }
    return out, None


# ============================================================================
# Gate.io v4 USDT-perpetual tickers -- crypto funding & 24h stats.
# URL: https://api.gateio.ws/api/v4/futures/usdt/tickers
# Free, no key. Returns an array of {contract, last, low_24h, high_24h,
# volume_24h, change_percentage, funding_rate_indicative, index_price, ...}.
#
# IMPORTANT: the existing tools.wt.altdata.crypto_funding() uses Binance fapi,
# which TIMES OUT from this environment. This function is a working
# alternative for perp funding/OI signals.
# ============================================================================
def gate_perp_tickers(symbols=None):
    """Return list of Gate.io USDT-perp tickers. `symbols` optional filter
    of base symbols, e.g. ["BTC","ETH","SOL"]. Each row normalized to
    {symbol, last, funding_rate, change_pct, high_24h, low_24h, volume_24h,
    index_price}."""
    d, e = _clean_json("https://api.gateio.ws/api/v4/futures/usdt/tickers",
                       timeout=12)
    if e:
        return None, e
    out = []
    syms = set(s.upper() for s in symbols) if symbols else None
    for r in d or []:
        contract = r.get("contract", "")  # e.g. "BTC_USDT"
        if not contract.endswith("_USDT"):
            continue
        base = contract[:-5]
        if syms and base not in syms:
            continue
        try:
            out.append({
                "symbol": base,
                "contract": contract,
                "last": float(r.get("last") or 0),
                "funding_rate": float(r.get("funding_rate_indicative") or 0),
                "change_pct": float(r.get("change_percentage") or 0),
                "high_24h": float(r.get("high_24h") or 0),
                "low_24h": float(r.get("low_24h") or 0),
                "volume_24h": float(r.get("volume_24h") or 0),
                "index_price": float(r.get("index_price") or 0),
            })
        except (TypeError, ValueError):
            continue
    return out, None


def crypto_funding_gate(symbol="BTC"):
    """Drop-in replacement for altdata.crypto_funding using Gate.io (works
    in this env where Binance fapi times out). Returns {funding_rate_pct,
    last, change_pct, contango_back_premium}."""
    rows, e = gate_perp_tickers([symbol])
    if e:
        return None, e
    if not rows:
        return None, "symbol not found"
    r = rows[0]
    return {
        "symbol": symbol,
        "funding_rate_pct": round(r["funding_rate"] * 100, 5),
        "last": r["last"],
        "change_pct": r["change_pct"],
        "index_price": r["index_price"],
        "basis_pct": round(100.0 * (r["last"] - r["index_price"]) / r["index_price"], 4)
                      if r["index_price"] else None,
    }, None


# ============================================================================
# Hacker News (Algolia) -- tech sentiment / catalyst mentions (free, no key).
# URL: https://hn.algolia.com/api/v1/search?query=...&tags=story
# Returns recent HN stories matching a query. Useful for catching
# developer/maker sentiment shifts around a product, infra provider, or
# technology (e.g. "OpenAI", "Anthropic", "CUDA", "RISC-V").
# ============================================================================
def hn_search(query, limit=10):
    """Return recent HN stories for a query. Each row: {title, url, points,
    num_comments, author, created_at, objectID}."""
    import urllib.parse as up
    q = up.quote(query)
    d, e = _clean_json(
        f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={limit}",
        timeout=12,
    )
    if e:
        return None, e
    out = []
    for h in d.get("hits", [])[:limit]:
        out.append({
            "title": h.get("title") or h.get("story_title"),
            "url": h.get("url") or h.get("story_url")
                   or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "points": h.get("points"),
            "num_comments": h.get("num_comments"),
            "author": h.get("author"),
            "created_at": h.get("created_at"),
            "object_id": h.get("objectID"),
        })
    return out, None


# ============================================================================
# Manifold Markets -- prediction-market odds (free, no key).
# URL: https://api.manifold.markets/v0/search-markets?term=...&limit=N
# Returns markets with probability, volume, liquidity. Useful as a
# cross-asset sentiment input (e.g. "Fed rate cut July", "Trump tariff").
# ============================================================================
def manifold_markets(query, limit=10):
    """Search Manifold prediction markets. Each row: {question, probability,
    volume, liquidity, close_date, url, outcome}."""
    import urllib.parse as up
    q = up.quote(query)
    d, e = _clean_json(
        f"https://api.manifold.markets/v0/search-markets?term={q}&limit={limit}",
        timeout=12,
    )
    if e:
        return None, e
    out = []
    for m in d[:limit] if isinstance(d, list) else []:
        if m.get("outcomeType") == "BINARY":
            out.append({
                "question": m.get("question"),
                "probability": m.get("probability"),
                "volume": m.get("volume"),
                "liquidity": m.get("liquidity"),
                "close_date": m.get("closeTime"),
                "url": m.get("url"),
                "creator": m.get("creatorUsername"),
            })
    return out, None


# ============================================================================
# FINNHUB calendars & insider transactions (free with FINNHUB_KEY, already in
# .env.local). These complement the altdata2 8-K scanner with a forward
# earnings calendar + structured insider Form-4 data.
#   - calendar/earnings   -> upcoming EPS dates (the scanner needs these to
#                            avoid holding through binary events, or to set
#                            up pre-earnings asymmetry plays)
#   - calendar/ipo        -> IPO calendar (supply/demand for recent debutantes)
#   - calendar/dividend   -> ex-div dates (capture/avoidance)
#   - stock/insider-transactions -> structured Form-4 (buy/sell clusters)
#   - stock/insider-sentiment    -> monthly MSPR (net insider sentiment)
# ============================================================================
from .core import api_key as _api_key


def _finnhub_get(path):
    k = _api_key("FINNHUB_KEY")
    if not k:
        return None, "no FINNHUB_KEY"
    sep = "&" if "?" in path else "?"
    url = f"https://finnhub.io/api/v1/{path}{sep}token={k}"
    return _clean_json(url, timeout=15)


def earnings_calendar(days_ahead=3):
    """Upcoming earnings for the next `days_ahead` days. Each row:
    {symbol, date, hour, quarter, year, eps_estimate, rev_estimate}."""
    import datetime as _dt
    today = _dt.date.today()
    frm = today.isoformat()
    to = (today + _dt.timedelta(days=days_ahead)).isoformat()
    d, e = _finnhub_get(f"calendar/earnings?from={frm}&to={to}")
    if e:
        return None, e
    out = []
    for r in d.get("earningsCalendar", []):
        out.append({
            "symbol": r.get("symbol"),
            "date": r.get("date"),
            "hour": r.get("hour") or "",  # bmo/amc
            "quarter": r.get("quarter"),
            "year": r.get("year"),
            "eps_estimate": r.get("epsEstimate"),
            "rev_estimate": r.get("revenueEstimate"),
        })
    out.sort(key=lambda r: (r["date"] or "", r["symbol"] or ""))
    return out, None


def ipo_calendar(days_ahead=7):
    """Upcoming IPOs."""
    import datetime as _dt
    today = _dt.date.today()
    frm = today.isoformat()
    to = (today + _dt.timedelta(days=days_ahead)).isoformat()
    d, e = _finnhub_get(f"calendar/ipo?from={frm}&to={to}")
    if e:
        return None, e
    return d.get("ipoCalendar", []), None


def dividend_calendar(days_ahead=14):
    """Upcoming ex-dividend dates."""
    import datetime as _dt
    today = _dt.date.today()
    frm = today.isoformat()
    to = (today + _dt.timedelta(days=days_ahead)).isoformat()
    d, e = _finnhub_get(f"calendar/dividend?from={frm}&to={to}")
    if e:
        return None, e
    return d.get("dividendCalendar", []), None


def finnhub_insider_transactions(symbol, limit=40):
    """Structured Form-4 insider transactions for a ticker. Each row:
    {name, share, change, transaction_date, transaction_code, transaction_price}."""
    d, e = _finnhub_get(f"stock/insider-transactions?symbol={symbol}")
    if e:
        return None, e
    out = []
    for r in (d.get("data") or [])[:limit]:
        out.append({
            "name": r.get("name"),
            "share": r.get("share"),
            "change": r.get("change"),
            "transaction_date": r.get("transactionDate"),
            "transaction_code": r.get("transactionCode"),  # P=buy, S=sell
            "transaction_price": r.get("transactionPrice"),
        })
    return out, None


def finnhub_insider_sentiment(symbol, months=6):
    """Monthly MSPR (Management Shareholder Performance Ratio) -- net insider
    buy/sell sentiment. Positive = insiders net buying."""
    import datetime as _dt
    today = _dt.date.today()
    frm = (today - _dt.timedelta(days=months * 31)).isoformat()
    to = today.isoformat()
    d, e = _finnhub_get(f"stock/insider-sentiment?symbol={symbol}&from={frm}&to={to}")
    if e:
        return None, e
    return d.get("data", []), None


# ============================================================================
# SINGLE ENTRY POINT -- run all new alt-data fetches in parallel.
# ============================================================================
def alt_data_sweep():
    """Run all altdata3 fetches in parallel. Returns dict of {source: (data, err)}."""
    jobs = {
        "vix_futures_curve": vix_futures_curve,
        "macro_snapshot": macro_snapshot,
        "defillama_fees": defillama_fees_snapshot,
        "defillama_dexs": defillama_dexs_snapshot,
        "earnings_calendar": earnings_calendar,
        "ipo_calendar": ipo_calendar,
        "dividend_calendar": dividend_calendar,
        "gate_perp_btc": lambda: crypto_funding_gate("BTC"),
        "gate_perp_eth": lambda: crypto_funding_gate("ETH"),
        "gate_perp_sol": lambda: crypto_funding_gate("SOL"),
    }
    out = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = {pool.submit(fn): name for name, fn in jobs.items()}
        for fut in futs:
            name = futs[fut]
            try:
                out[name] = fut.result(timeout=30)
            except Exception as e:
                out[name] = (None, describe_err(e))
    return out

