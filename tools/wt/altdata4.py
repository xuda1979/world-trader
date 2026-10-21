"""altdata4 -- new free data sources added 2026-09-07.

All sources here are FREE and need NO API key. Each fetcher returns
(data, err) consistent with the rest of the package.

Sources in this module (all verified reachable from this env on 2026-09-07;
same flaky-proxy caveat as altdata3 -- everything goes through _clean_get):

  - CoinGecko trending + global     -> crypto retail attention & mcap regime
  - Wikipedia pageviews API         -> per-name retail attention (leading
                                       indicator for meme/retail flows)
  - EPU index (policyuncertainty)   -> US policy uncertainty regime (monthly)
  - Treasury DTS (fiscaldata API)   -> TGA cash balance (liquidity regime)
  - USAspending award search        -> who is winning federal money
                                       (CHIPS/defense/IRA policy catalysts)
  - ClinicalTrials.gov v2           -> trial-count density + recent starts
                                       (biotech catalyst radar)
  - openFDA enforcement + drugsfda  -> recalls and approvals (pharma flags)
  - Open-Meteo forecast+archive     -> weather anomalies (ag/energy input:
                                       frost -> coffee/OJ, storm -> energy)
  - Ken French factors ZIP          -> daily MKT-RF/SMB/HML/RF benchmark
                                       factors for cross-sectional work

Probed and REJECTED on 2026-09-07 (blocked or client-rendered from this env):
  CNN fear&greed (HTTP 418), NY Fed markets API (HTTP 400 on all paths),
  fiscaldata operating_cash_balance/auctions-query (404), SEC threshold
  list (403), Atlanta Fed GDPNow (client-rendered, no data API in page),
  FRED graph CSV (timed out; altdata3 already covers keyless FRED).
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from .core import http_get, http_post, describe_err

import datetime as _dt
import io as _io
import json as _json
import re as _re
import time as _time
import urllib.parse as _urlparse
import urllib.request as _urlreq
import zipfile as _zipfile

# ---------------------------------------------------------------------------
# Resilient fetch helpers (same rationale as altdata3: this network has a
# flaky transparent proxy that intermittently serves a captive-portal page).
# ---------------------------------------------------------------------------
_PORTAL_RE = _re.compile("\u7528\u6237\u8ba4\u8bc1\u7cfb\u7edf|\u8ba4\u8bc1\u7cfb\u7edf|\u4e2a\u4eba\u8ba4\u8bc1|\u767b\u5f55\u9a8c\u8bc1")

# Some endpoints (Wikimedia, .gov APIs) prefer a browser-ish UA.
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


def _http_get_bytes(url, *, headers=None, timeout=30):
    """Raw binary GET (http_get decodes to str, which corrupts ZIP payloads).
    Raises on error; callers wrap."""
    h = dict()
    h["User-Agent"] = _BROWSER_UA
    h["Accept"] = "*/*"
    if headers:
        h.update(headers)
    req = _urlreq.Request(url, headers=h)
    with _urlreq.urlopen(req, timeout=timeout) as r:
        return r.read()


# ============================================================================
# CoinGecko -- trending coins (retail attention) + global mcap regime.
#   https://api.coingecko.com/api/v3/search/trending
#   https://api.coingecko.com/api/v3/global
# Free tier: no key, ~10-30 req/min -- keep call counts low.
# ============================================================================
def coingecko_trending(limit=7):
    d, e = _clean_json("https://api.coingecko.com/api/v3/search/trending")
    if e:
        return None, e
    try:
        coins = d.get("coins", [])[:limit]
        rows = []
        for i, c in enumerate(coins):
            it = c.get("item") or dict()
            rows.append(dict(rank=i + 1,
                             id=it.get("id"),
                             symbol=it.get("symbol"),
                             name=it.get("name"),
                             mcap_rank=it.get("market_cap_rank")))
        return rows, None
    except Exception as e:
        return None, describe_err(e)


def coingecko_global():
    d, e = _clean_json("https://api.coingecko.com/api/v3/global")
    if e:
        return None, e
    try:
        data = d.get("data") or dict()
        mcap = data.get("total_market_cap") or dict()
        dom = data.get("market_cap_percentage") or dict()
        out = dict(
            total_mcap_usd=mcap.get("usd"),
            mcap_change_24h_pct=data.get("market_cap_change_percentage_24h_usd"),
            btc_dominance_pct=dom.get("btc"),
            eth_dominance_pct=dom.get("eth"),
            active_cryptocurrencies=data.get("active_cryptocurrencies"),
        )
        return out, None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# Wikipedia pageviews -- retail attention proxy.
#   .../per-article/en.wikipedia/all-access/user/{article}/daily/{s}/{e}
#   .../top/en.wikipedia/all-access/{y}/{m}/{d}          (daily top-1000)
# No key. 404 on a name with no data yet -> treat as empty, not error.
# ============================================================================
def _ymd_from_ts(ts):
    return ts[:4] + "-" + ts[4:6] + "-" + ts[6:8]


def wikipedia_pageviews(article, days=14):
    end = _dt.date.today()
    start = end - _dt.timedelta(days=max(1, days) - 1)
    art = _re.sub(r"\s+", "_", article.strip())
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
           "/en.wikipedia/all-access/user/%s/daily/%s/%s"
           % (_urlparse.quote(art), start.strftime("%Y%m%d"),
              end.strftime("%Y%m%d")))
    d, e = _clean_json(url)
    if e:
        if "HTTP 404" in str(e):        # no pageview rows yet -> empty, not err
            return [], None
        return None, e
    try:
        rows = [(_ymd_from_ts(it["timestamp"]), int(it["views"]))
                for it in d.get("items", [])]
        return rows, None
    except Exception as e:
        return None, describe_err(e)


_MAINPAGE_RE = _re.compile(r"^(Main_Page|Special:|Wikipedia:|Portal:|Help:)",
                           _re.I)


def wikipedia_top_views(date=None, limit=15):
    """Daily top-viewed en-Wikipedia attention radar, minus nav pages."""
    if date:
        d0 = _dt.date.fromisoformat(date)
    else:
        d0 = _dt.date.today() - _dt.timedelta(days=2)   # top-1000 lags ~2 days
    url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/top"
           "/en.wikipedia/all-access/%s" % d0.strftime("%Y/%m/%d"))
    d, e = _clean_json(url)
    if e:
        if "HTTP 404" in str(e):
            return [], None
        return None, e
    try:
        arts = (d.get("items") or [dict()])[0].get("articles") or []
        rows = []
        for a in arts:
            name = a.get("article") or ""
            if _MAINPAGE_RE.match(name):
                continue
            rows.append(dict(rank=len(rows) + 1, article=name,
                             views=a.get("views")))
            if len(rows) >= int(limit):
                break
        return rows, None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# Economic Policy Uncertainty index (Baker-Bloom-Davis), monthly CSV.
#   https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.csv
# ============================================================================
def epu_index(months=14):
    txt, e = _clean_get(
        "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.csv")
    if e:
        return None, e
    try:
        rows = []
        for ln in txt.splitlines()[1:]:
            parts = [p.strip() for p in ln.split(",")]
            if len(parts) < 3 or not parts[0].isdigit():
                continue
            rows.append(dict(ym="%04d-%02d" % (int(parts[0]), int(parts[1])),
                             epu=float(parts[2])))
        return rows[-int(months):], None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# Treasury DTS via fiscaldata.treasury.gov -> TGA cash balance (liquidity).
#   /v1/accounting/dts/deposits_withdrawals_operating_cash
# TGA draw = liquidity drain (risk-off); TGA spend = liquidity add.
# NOTE: only this DTS endpoint answers from this env; operating_cash_balance
# and auctions-query 404 here (verified 2026-09-07).
# ============================================================================
_TGA = "Treasury General Account (TGA)"


def treasury_tga_flow(days=10):
    """Net daily operating-cash flow ($ millions) for the TGA, aggregated
    from DTS Deposits/Withdrawals line items (verified 2026-09-07: this DTS
    table exposes transaction amounts only -- the balance endpoints 404
    from this env). Positive = net deposit (cash build), negative = net
    withdrawal (liquidity add to the private sector)."""
    q = _urlparse.quote(_TGA)
    url = ("https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
           "/v1/accounting/dts/deposits_withdrawals_operating_cash"
           "?filter=account_type:eq:" + q +
           "&sort=-record_date&page%5Bsize%5D=2000&format=json")
    d, e = _clean_json(url)
    if e:
        return None, e
    try:
        by_date = {}
        order = []
        for r in d.get("data", []):
            dt = r.get("record_date")
            if not dt:
                continue
            if dt not in by_date:
                by_date[dt] = dict(date=dt, deposits_mm=0.0,
                                   withdrawals_mm=0.0)
                order.append(dt)
            try:
                amt = float(r.get("transaction_today_amt") or 0)
            except (TypeError, ValueError):
                continue
            bucket = by_date[dt]
            if r.get("transaction_type") == "Deposits":
                bucket["deposits_mm"] += amt
            else:
                bucket["withdrawals_mm"] += amt
        rows = []
        for dt in order[:int(days)]:
            b = by_date[dt]
            b["net_mm"] = round(b["deposits_mm"] - b["withdrawals_mm"], 1)
            b["deposits_mm"] = round(b["deposits_mm"], 1)
            b["withdrawals_mm"] = round(b["withdrawals_mm"], 1)
            rows.append(b)
        return rows, None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# USAspending -- federal award search (policy-catalyst radar: who is winning
# CHIPS / defense / IRA money). POST /api/v2/search/spending_by_award/
# ============================================================================
_USA_AWARD_TYPES = ["A", "B", "C", "D"]   # contract award type codes


def usaspending_awards(keyword, days=30, limit=10):
    end = _dt.date.today()
    start = end - _dt.timedelta(days=max(1, days))
    tp = dict()
    tp["start_date"] = start.isoformat()
    tp["end_date"] = end.isoformat()
    filters = dict()
    filters["award_type_codes"] = list(_USA_AWARD_TYPES)
    filters["time_period"] = [tp]
    filters["keywords"] = [keyword]
    payload = dict()
    payload["filters"] = filters
    payload["fields"] = ["Award ID", "Recipient Name", "Award Amount",
                         "Description", "Start Date"]
    payload["limit"] = int(limit)
    payload["page"] = 1
    body = _json.dumps(payload).encode()
    h = dict()
    h["Content-Type"] = "application/json"
    last_err = None
    for attempt in range(3):
        try:
            txt = http_post(
                "https://api.usaspending.gov/api/v2/search/spending_by_award/",
                headers=h, body=body, timeout=25)
            d = _json.loads(txt)
            rows = []
            for r in d.get("results", []):
                row = dict()
                row["award_id"] = r.get("Award ID")
                row["recipient"] = r.get("Recipient Name")
                row["amount_usd"] = r.get("Award Amount")
                row["description"] = r.get("Description")
                row["start_date"] = r.get("Start Date")
                rows.append(row)
            return rows, None
        except Exception as e:
            last_err = describe_err(e)
            _time.sleep(0.4 * (attempt + 1))
    return None, last_err


# ============================================================================
# ClinicalTrials.gov v2 -- biotech catalyst radar.
#   .../studies?query.cond={cond}&countTotal=true
#   .../studies?query.cond={cond}&sort=LastUpdatePostDate:desc&pageSize=N
# ============================================================================
def clinical_trials_count(condition):
    url = ("https://clinicaltrials.gov/api/v2/studies?query.cond=%s"
           "&countTotal=true&pageSize=1&fields=NCTId"
           % _urlparse.quote(condition))
    d, e = _clean_json(url)
    if e:
        return None, e
    try:
        return int(d.get("totalCount", 0)), None
    except Exception as e:
        return None, describe_err(e)


def clinical_trials_recent(condition, limit=10):
    url = ("https://clinicaltrials.gov/api/v2/studies?query.cond=%s"
           "&sort=LastUpdatePostDate:desc&pageSize=%d"
           "&fields=NCTId,BriefTitle,OverallStatus,LeadSponsorName,StartDate"
           % (_urlparse.quote(condition), int(limit)))
    d, e = _clean_json(url)
    if e:
        return None, e
    try:
        rows = []
        for s in d.get("studies", []):
            p = s.get("protocolSection") or dict()
            ident = p.get("identificationModule") or dict()
            status = p.get("statusModule") or dict()
            spon = p.get("sponsorCollaboratorsModule") or dict()
            rows.append(dict(
                nct_id=ident.get("nctId"),
                title=ident.get("briefTitle"),
                overall_status=status.get("overallStatus"),
                lead_sponsor=(spon.get("leadSponsor") or dict()).get("name"),
                start_date=(status.get("startDateStruct") or dict()).get("date"),
            ))
        return rows, None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# openFDA -- drug recalls (enforcement) and approvals (drugsfda).
#   https://api.fda.gov/drug/enforcement.json?search=report_date:[..]
#   https://api.fda.gov/drug/drugsfda.json?search=submissions:..
# No key at low volume (240 req/min per IP unauthenticated).
# ============================================================================
def fda_enforcement(days=30, limit=10):
    end = _dt.date.today()
    start = end - _dt.timedelta(days=max(1, days))
    url = ("https://api.fda.gov/drug/enforcement.json"
           "?search=report_date:[%s+TO+%s]&limit=%d"
           % (start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), int(limit)))
    d, e = _clean_json(url)
    if e:
        if "HTTP 404" in str(e):        # no recalls in window -> empty, not err
            return [], None
        return None, e
    try:
        rows = []
        for r in d.get("results", []):
            of = r.get("openfda") or dict()
            rows.append(dict(
                brand=(of.get("brand_name") or [None])[0],
                reason=r.get("reason_for_recall"),
                classification=r.get("classification"),
                date=r.get("report_date"),
                status=r.get("status"),
                product_qty=r.get("product_quantity"),
            ))
        return rows, None
    except Exception as e:
        return None, describe_err(e)


def fda_approvals(days=30, limit=10):
    end = _dt.date.today()
    start = end - _dt.timedelta(days=max(1, days))
    # openFDA status codes: AP=approved, TA=tentative approval; dates YYYYMMDD
    url = ("https://api.fda.gov/drug/drugsfda.json"
           "?search=submissions.submission_status:AP"
           "+AND+submissions.submission_status_date:[%s+TO+%s]&limit=%d"
           % (start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), int(limit)))
    d, e = _clean_json(url)
    if e:
        if "HTTP 404" in str(e):
            return [], None
        return None, e
    try:
        rows = []
        for r in d.get("results", []):
            of = r.get("openfda") or dict()
            brand = (of.get("brand_name") or [None])[0]
            for s in r.get("submissions", []):
                code = (s.get("submission_status") or "").upper()
                if code not in ("AP", "TA"):
                    continue
                raw = s.get("submission_status_date") or ""
                date = (raw[:4] + "-" + raw[4:6] + "-" + raw[6:]
                        if _re.match(r"^\d{8}$", raw) else raw)
                rows.append(dict(
                    brand=brand,
                    applicant=r.get("sponsor_name"),
                    submission_type=s.get("submission_type"),
                    submission_number=s.get("submission_number"),
                    tentative=(code == "TA"),
                    date=date,
                ))
        rows.sort(key=lambda x: x.get("date") or "", reverse=True)
        return rows[:int(limit)], None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# Open-Meteo -- weather anomalies as ag/energy commodity input (free, no key).
#   forecast:  https://api.open-meteo.com/v1/forecast?...&past_days=N
#   archive:   https://archive-api.open-meteo.com/v1/archive?...
# ============================================================================
def weather_snapshot(lat, lon, past_days=7, forecast_days=7):
    url = ("https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
           "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
           "&temperature_unit=fahrenheit&precipitation_unit=inch"
           "&past_days=%d&forecast_days=%d&timezone=auto"
           % (lat, lon, max(1, int(past_days)), max(1, int(forecast_days))))
    d, e = _clean_json(url)
    if e:
        return None, e
    try:
        daily = d.get("daily") or dict()
        dates = daily.get("time") or []
        rows = []
        tmax_l = daily.get("temperature_2m_max") or []
        tmin_l = daily.get("temperature_2m_min") or []
        prcp_l = daily.get("precipitation_sum") or []
        for i in range(len(dates)):
            rows.append(dict(
                date=dates[i],
                tmax_f=tmax_l[i] if i < len(tmax_l) else None,
                tmin_f=tmin_l[i] if i < len(tmin_l) else None,
                precip_in=prcp_l[i] if i < len(prcp_l) else None,
            ))
        out = dict(lat=d.get("latitude"), lon=d.get("longitude"),
                   tz=d.get("timezone"), daily=rows)
        hist = [r for r in rows if r["tmax_f"] is not None]
        if len(hist) >= 2:
            tmax = [r["tmax_f"] for r in hist]
            out["recent_tmax_mean_f"] = round(sum(tmax) / len(tmax), 1)
            out["recent_precip_total_in"] = round(
                sum(r["precip_in"] or 0 for r in hist), 2)
        return out, None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# Ken French research factors -- daily MKT-RF / SMB / HML / RF benchmark.
#   https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/
#       F-F_Research_Data_Factors_daily_CSV.zip
# Binary ZIP -> needs _http_get_bytes (http_get's utf-8 decode corrupts it).
# ============================================================================
def _parse_french_csv(txt):
    """Shared parser (unit-tested offline). Stops at the trailing annual
    factors section; returns rows of {date, mkt_rf_pct, smb_pct, hml_pct,
    rf_pct}."""
    rows = []
    for ln in txt.splitlines():
        parts = [p.strip() for p in ln.split(",")]
        if len(parts) < 5 or not _re.match(r"^\d{8}$", parts[0]):
            if rows:
                break       # trailing "Annual Factors" section -> stop
            continue
        d0 = parts[0]
        rows.append(dict(
            date=d0[:4] + "-" + d0[4:6] + "-" + d0[6:],
            mkt_rf_pct=float(parts[1]),
            smb_pct=float(parts[2]),
            hml_pct=float(parts[3]),
            rf_pct=float(parts[4]),
        ))
    return rows


def french_factors_daily(days=60):
    try:
        raw = _http_get_bytes(
            "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
            "F-F_Research_Data_Factors_daily_CSV.zip", timeout=45)
        zf = _zipfile.ZipFile(_io.BytesIO(raw))
        txt = zf.read(zf.namelist()[0]).decode("latin-1")
    except Exception as e:
        return None, describe_err(e)
    try:
        rows = _parse_french_csv(txt)
        if not rows:
            return None, "no daily factor rows parsed"
        return rows[-int(days):], None
    except Exception as e:
        return None, describe_err(e)


# ============================================================================
# SINGLE ENTRY POINT -- run all keyless fetches in parallel.
# ============================================================================
def alt_data_sweep():
    """Run all altdata4 fetches in parallel. Returns dict of (source: (data, err))."""
    jobs = dict(
        coingecko_trending=coingecko_trending,
        coingecko_global=coingecko_global,
        wikipedia_top_views=wikipedia_top_views,
        epu_index=epu_index,
        treasury_tga=treasury_tga_flow,
        clinical_trials_obesity=lambda: clinical_trials_count("obesity"),
        fda_enforcement=fda_enforcement,
        fda_approvals=fda_approvals,
        weather_chicago=lambda: weather_snapshot(41.88, -87.63),
        french_factors=french_factors_daily,
        wiki_tesla_pageviews=lambda: wikipedia_pageviews("Tesla,_Inc."),
        usaspending_chips=lambda: usaspending_awards("semiconductors"),
    )
    out = dict()
    with ThreadPoolExecutor(max_workers=6) as pool:
        futs = dict()
        for name, fn in jobs.items():
            futs[pool.submit(fn)] = name
        for fut in futs:
            name = futs[fut]
            try:
                out[name] = fut.result(timeout=60)
            except Exception as e:
                out[name] = (None, describe_err(e))
    return out
