"""Catalyst calendar: upcoming, dated, tradeable events that produce asymmetric
short-term moves -- earnings, FDA/PDUFA, IPOs, large dividends, and (where free
data exists) macro releases. These are NOT signals on their own; they are
*bounded-risk windows* where a position with a defined stop has a known,
calendar-driven exit/catalyst date.

Design:
  - Free data only: Finnhub (earnings/IPO/FDA), Polygon (dividends).
  - Each catalyst returns a normalized record:
      {sym, date(ISO), kind, hour, eps_est, rev_est, detail}
  - `for_symbols(syms, days=14)` returns only catalysts for the given universe
    -- this is the integration point for scan.py.
  - `upcoming(days=14)` returns ALL upcoming catalysts (for the standalone
    "CATALYST CALENDAR" scan section).

Catalyst-aware scoring (used by analysis.py via report.py):
  - A row with a catalyst within `days` gets a small `catalyst_boost` to its
    composite score AND a `catalyst_date` field so the trade plan can show
    "exit by <date>".
  - The boost is capped; a catalyst is an opportunity to express an existing
    edge, not a substitute for one.
"""
from __future__ import annotations
import datetime, threading
from concurrent.futures import ThreadPoolExecutor
from . import core

UA = core.UA
_LOCK = threading.Lock()
_CACHE: dict = {}  # key -> (ts, payload)
_TTL = 6 * 3600  # 6h -- catalysts don't move fast

# ---------------------------------------------------------------- _get
def _get(url):
    """JSON GET with UA + timeout. Returns (data, err)."""
    try:
        import urllib.request, json
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, core.describe_err(e)

def _cached(key, fn):
    """Simple TTL cache so repeated scans don't re-hit endpoints."""
    now = datetime.datetime.now().timestamp()
    with _LOCK:
        hit = _CACHE.get(key)
        if hit and (now - hit[0]) < _TTL:
            return hit[1]
    val = fn()
    with _LOCK:
        _CACHE[key] = (now, val)
    return val

def _today_plus(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()

# ---------------------------------------------------------------- earnings
def earnings_calendar(from_date=None, to_date=None, days=14):
    """Finnhub earnings calendar. Returns list of normalized records."""
    k = core.api_key("FINNHUB_KEY")
    if not k:
        return [], "no FINNHUB_KEY"
    from_date = from_date or datetime.date.today().isoformat()
    to_date = to_date or _today_plus(days)
    url = (f"https://finnhub.io/api/v1/calendar/earnings"
           f"?from={from_date}&to={to_date}&token={k}")
    d, err = _get(url)
    if err:
        return [], err
    out = []
    for e in (d.get("earningsCalendar") or []):
        out.append({
            "sym": e.get("symbol"),
            "date": e.get("date"),
            "kind": "earnings",
            "hour": e.get("hour", "") or "",  # bmo/amc/dmkt
            "eps_est": e.get("epsEstimate"),
            "rev_est": e.get("revenueEstimate"),
            "quarter": e.get("quarter"),
            "year": e.get("year"),
            "detail": (f"Q{e.get('quarter')} {e.get('year')} "
                       f"EPS est {e.get('epsEstimate')}"),
        })
    return out, None

# ---------------------------------------------------------------- IPO
def ipo_calendar(from_date=None, to_date=None, days=14):
    """Finnhub IPO calendar. New listings often create short-term momentum."""
    k = core.api_key("FINNHUB_KEY")
    if not k:
        return [], "no FINNHUB_KEY"
    from_date = from_date or datetime.date.today().isoformat()
    to_date = to_date or _today_plus(days)
    url = (f"https://finnhub.io/api/v1/calendar/ipo"
           f"?from={from_date}&to={to_date}&token={k}")
    d, err = _get(url)
    if err:
        return [], err
    out = []
    for e in (d.get("ipoCalendar") or []):
        sym = e.get("symbol") or e.get("name")
        out.append({
            "sym": sym,
            "date": e.get("date"),
            "kind": "ipo",
            "hour": "",
            "eps_est": None,
            "rev_est": None,
            "detail": f"IPO {e.get('name','')} ${e.get('priceRange','?')}",
        })
    return out, None

# ---------------------------------------------------------------- FDA
def fda_calendar(from_date=None, to_date=None, days=45):
    """Finnhub FDA/PDUFA calendar. Biotech catalysts -- very high variance."""
    k = core.api_key("FINNHUB_KEY")
    if not k:
        return [], "no FINNHUB_KEY"
    from_date = from_date or datetime.date.today().isoformat()
    to_date = to_date or _today_plus(days)
    url = (f"https://finnhub.io/api/v1/calendar/fda"
           f"?from={from_date}&to={to_date}&token={k}")
    d, err = _get(url)
    if err:
        return [], err
    out = []
    for e in (d.get("fdaCalendar") or []):
        out.append({
            "sym": e.get("symbol"),
            "date": e.get("date"),
            "kind": "fda",
            "hour": "",
            "eps_est": None,
            "rev_est": None,
            "detail": f"FDA {e.get('stage','')} {e.get('panel','')}".strip(),
        })
    return out, None

# ---------------------------------------------------------------- dividends
def dividends_calendar(from_date=None, to_date=None, days=14):
    """Polygon dividends. Large/special dividends can move prices."""
    k = core.api_key("POLYGON_KEY")
    if not k:
        return [], "no POLYGON_KEY"
    from_date = from_date or datetime.date.today().isoformat()
    to_date = to_date or _today_plus(days)
    url = (f"https://api.polygon.io/v3/reference/dividends?apiKey={k}"
           f"&ex_dividend_date.gte={from_date}&ex_dividend_date.lte={to_date}"
           f"&limit=1000&sort=ex_dividend_date")
    d, err = _get(url)
    if err:
        return [], err
    out = []
    for e in (d.get("results") or []):
        amt = e.get("cash_amount") or 0
        try:
            amt_f = float(amt)
        except (TypeError, ValueError):
            amt_f = 0.0
        # only flag meaningful dividends (> $0.50 or 'special' type)
        if amt_f < 0.50 and (e.get("dividend_type") or "") != "SC":
            continue
        out.append({
            "sym": e.get("ticker"),
            "date": e.get("ex_dividend_date"),
            "kind": "dividend",
            "hour": "",
            "eps_est": None,
            "rev_est": None,
            "amount": amt_f,
            "freq": e.get("frequency"),
            "detail": f"div ${amt_f:.4f} ({e.get('dividend_type','')})",
        })
    return out, None

# ---------------------------------------------------------------- aggregate
def upcoming(days=14):
    """All upcoming catalysts across all sources, deduped by (sym, date, kind)."""
    out = []
    errs = []
    # parallel fetch -- each source is independent
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(earnings_calendar, None, None, days): "earnings",
            ex.submit(ipo_calendar, None, None, days): "ipo",
            ex.submit(fda_calendar, None, None, days): "fda",
            ex.submit(dividends_calendar, None, None, days): "dividends",
        }
        for fut, name in futs.items():
            try:
                rows, err = fut.result()
                if err:
                    errs.append(f"{name}: {err}")
                else:
                    out.extend(rows)
            except Exception as e:
                errs.append(f"{name}: {core.describe_err(e)}")
    # dedupe
    seen = set()
    deduped = []
    for r in out:
        key = (r.get("sym"), r.get("date"), r.get("kind"))
        if key in seen or not r.get("sym") or not r.get("date"):
            continue
        seen.add(key)
        deduped.append(r)
    # sort by date then kind
    deduped.sort(key=lambda r: (r.get("date") or "", r.get("kind") or ""))
    return deduped, errs

def for_symbols(syms, days=14):
    """Catalysts for a specific symbol set (used to enrich opportunity rows)."""
    syms = {str(s).upper() for s in syms if s}
    all_cal, _ = upcoming(days=days)
    out = [r for r in all_cal if (r.get("sym") or "").upper() in syms]
    return out

def catalyst_for(sym, days=14):
    """Single-symbol lookup. Returns the nearest upcoming catalyst or None."""
    rows = for_symbols([sym], days=days)
    if not rows:
        return None
    rows.sort(key=lambda r: r.get("date") or "9999")
    return rows[0]

# ---------------------------------------------------------------- print
def _is_actionable_ticker(sym):
    """Filter OTC/pink/ADR-noise tickers from the calendar display.
    Heuristic: real US listings are 1-5 uppercase letters, no dots, no 5-char
    OTC suffixes like ZHUZY/REPYY/XOMAP. We keep anything 1-4 chars or in the
    curated set of common ADRs."""
    if not sym:
        return False
    s = str(sym).upper().strip()
    if "." in s:  # .HK/.SS/.SZ/.T etc -- keep, those are real foreign listings
        return True
    if not s.isalpha():
        return False
    # 5-char OTC tickers (the dividend-calendar spam): keep only if they're
    # in our known-good set. Practically: drop 5-char all-alpha OTC names.
    if len(s) >= 5:
        return False
    return True

def print_calendar(days=14, limit=40, earnings_only=False):
    """Standalone pretty-print of upcoming catalysts. Filters OTC/ADR dividend
    noise so the displayed calendar is actionable US-listed events."""
    rows, errs = upcoming(days=days)
    # filter to actionable
    rows = [r for r in rows if _is_actionable_ticker(r.get("sym"))]
    if earnings_only:
        rows = [r for r in rows if r.get("kind") in ("earnings", "fda", "ipo")]
    # always show earnings/FDA first, dividends last
    kind_order = {"earnings": 0, "fda": 1, "ipo": 2, "dividend": 3}
    rows.sort(key=lambda r: (r.get("date") or "9999",
                              kind_order.get(r.get("kind"), 9),
                              r.get("sym") or ""))
    today = datetime.date.today().isoformat()
    print(f"\n-- CATALYST CALENDAR (next {days}d; today={today}) --")
    if not rows:
        print("  (no actionable upcoming catalysts found)")
        if errs:
            print("  errors: " + "; ".join(errs))
        return
    # group by date
    by_date = {}
    for r in rows:
        by_date.setdefault(r["date"], []).append(r)
    n = 0
    for d in sorted(by_date.keys()):
        if n >= limit:
            break
        items = by_date[d]
        # within a day, earnings/FDA first
        items.sort(key=lambda r: kind_order.get(r.get("kind"), 9))
        print(f"  {d}  ({len(items)})")
        for r in items[:8]:
            tag = {"earnings":"ERN","ipo":"IPO","fda":"FDA","dividend":"DIV"}.get(r["kind"], r["kind"][:3].upper())
            extra = ""
            if r.get("eps_est") is not None:
                extra = f" EPS~{r['eps_est']}"
            if r.get("amount"):
                extra = f" ${r['amount']:.2f}"
            sym = (r.get("sym") or "----").ljust(7)
            print(f"    [{tag}] {sym}  {(r.get('detail') or '').strip()[:80]}{extra}")
            n += 1
            if n >= limit:
                break
    if errs:
        print(f"  (source errors: {'; '.join(errs)})")

if __name__ == "__main__":
    print_calendar(days=14)
