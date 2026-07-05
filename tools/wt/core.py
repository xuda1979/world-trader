"""Shared infrastructure: HTTP, API keys, CJK-aware tables, freshness, math."""
from __future__ import annotations
import json, os, ssl, statistics, urllib.request, urllib.error
import unicodedata
from datetime import datetime, timezone

UA = "Mozilla/5.0 (world-trader; research only)"
TIMEOUT = 12
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

# ---------------------------------------------------------------- HTTP
def http_get(url, *, headers=None, decode="utf-8", timeout=TIMEOUT):
    """GET a URL, return decoded text. Raises on HTTP/network error."""
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode(decode, "replace")

def get_json(url, **kw):
    return json.loads(http_get(url, **kw))

def describe_err(e):
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return f"net: {e.reason}"
    if isinstance(e, TimeoutError):
        return "timeout"
    return f"{type(e).__name__}: {str(e)[:50]}"

# ---------------------------------------------------------------- keys
_ENV_PATHS = (".env.local",
              os.path.join(os.path.dirname(__file__), "..", "..", ".env.local"))
_KEYCACHE = {}
def api_key(name):
    """Read an API key from env or .env.local (gitignored). Cached."""
    if name in _KEYCACHE:
        return _KEYCACHE[name]
    val = os.environ.get(name, "")
    if not val:
        for p in _ENV_PATHS:
            try:
                for line in open(p):
                    if line.startswith(name + "="):
                        val = line.split("=", 1)[1].strip()
                        break
            except OSError:
                continue
            if val:
                break
    _KEYCACHE[name] = val
    return val

# ---------------------------------------------------------------- time
try:
    from zoneinfo import ZoneInfo
    _EST = ZoneInfo("America/New_York")  # EST/EDT, DST-aware
except Exception:                        # pragma: no cover
    from datetime import timedelta
    _EST = timezone(timedelta(hours=-5))  # fixed-offset fallback

# Per-market local timezone (IANA). Used to render quote times in the
# instrument's native wall-clock -- a CN-A quote at 15:14 Beijing should
# READ "15:14 Asia/Shanghai", not "03:14 ET". Falls back to a fixed offset
# if ZoneInfo isn't available.
_MARKET_TZ = {}
def _market_tz(market):
    m = (market or "").upper()
    if m in _MARKET_TZ:
        return _MARKET_TZ[m]
    iana = {
        "CN-A": "Asia/Shanghai",
        "HK":   "Asia/Hong_Kong",
        "TW":   "Asia/Taipei",
        "US":   "America/New_York",
        "FX":   "UTC",          # FX is 24/5; UTC is the canonical stamp
        "CRYPTO": "UTC",        # crypto is 24/7; UTC is canonical
        "FUT":  "America/New_York",
        "IDX":  "UTC",
    }.get(m, "UTC")
    try:
        tz = ZoneInfo(iana)
    except Exception:
        from datetime import timedelta
        offsets = {"CN-A": 8, "HK": 8, "TW": 8, "US": -5, "FX": 0,
                   "CRYPTO": 0, "FUT": -5, "IDX": 0}
        tz = timezone(timedelta(hours=offsets.get(m, 0)))
    _MARKET_TZ[m] = tz
    return tz

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _to_epoch(ts):
    """Best-effort parse of a quote timestamp into a UTC epoch (float seconds).

    Accepts: int/float epoch (sec or ms), numeric strings, and a few common
    provider date/datetime string forms. Returns None if it can't be parsed to
    a *time of day* -- a bare DATE (e.g. 'Jun 29, 2026') is intentionally NOT
    treated as fresh, because a date-only stamp means we don't actually know the
    intraday trade time and must not present it as a live, actionable price.
    """
    if ts is None or ts == "":
        return None
    # numeric epoch (sec, or ms if absurdly large)
    try:
        v = float(ts)
        if v > 1e11:          # milliseconds
            v /= 1000.0
        if v > 1e8:           # plausible epoch seconds (>= ~1973)
            return v
    except (TypeError, ValueError):
        pass
    s = str(ts).strip().replace(" ET", "").replace(" EDT", "").replace(" EST", "")
    # datetime forms WITH a clock time -> usable; pure dates -> reject (return None)
    fmts = ("%b %d, %Y %H:%M:%S", "%b %d, %Y %I:%M %p", "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M")
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            # Nasdaq trade times are US Eastern; localize then to UTC.
            return dt.replace(tzinfo=_EST).timestamp()
        except (ValueError, NameError):
            continue
    return None

def age_seconds(ts):
    """Seconds since a quote ts. None if missing/invalid/date-only (not fresh)."""
    e = _to_epoch(ts)
    if e is None:
        return None
    return (datetime.now(timezone.utc) - datetime.fromtimestamp(e, timezone.utc)).total_seconds()

def est_time(ts):
    """Format a quote ts as 'YYYY-MM-DD HH:MM ET' in US Eastern (DST-aware).
    Long form so the full date (year-month-day) + time of the quote is explicit.
    '' if none/unparseable."""
    e = _to_epoch(ts)
    if e is None:
        return ""
    try:
        dt = datetime.fromtimestamp(e, timezone.utc).astimezone(_EST)
        return dt.strftime("%Y-%m-%d %H:%M ET")
    except Exception:
        return ""

def local_time(ts, market):
    """Format a quote ts as 'MM-DD HH:MM' in the instrument's LOCAL timezone
    (Beijing for CN-A, Taipei for TW, Hong Kong for HK, New York for US,
    UTC for FX/CRYPTO). Returns '--' if ts is missing/unparseable.

    Why local: a trader in front of a CN-A quote thinks in Beijing time;
    showing ET would force a mental conversion every read. The freshness
    gate still uses the UTC epoch internally, so this is purely a display
    concern."""
    e = _to_epoch(ts)
    if e is None:
        return ""
    try:
        tz = _market_tz(market)
        dt = datetime.fromtimestamp(e, timezone.utc).astimezone(tz)
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        return ""

MAX_STALE_S = 15 * 60
def freshness(ts):
    """(age_seconds, label). RT/CLOSED/STALE/no-ts."""
    age = age_seconds(ts)
    if age is None:
        return None, "no-ts"
    m = age / 60
    if age <= MAX_STALE_S:
        return age, f"RT {m:.0f}m"
    if age <= 16 * 3600:
        return age, f"CLOSED {m/60:.1f}h"
    return age, f"STALE {m/60:.1f}h"

# ---------------------------------------------------------------- CJK tables
def display_width(s):
    """Visual width counting CJK/wide glyphs as 2 columns."""
    w = 0
    for ch in str(s):
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w

def pad(s, width, align="left"):
    """Pad string to a visual width, CJK-aware. align: left|right|center."""
    s = str(s)
    gap = width - display_width(s)
    if gap <= 0:
        return s
    if align == "right":
        return " " * gap + s
    if align == "center":
        l = gap // 2
        return " " * l + s + " " * (gap - l)
    return s + " " * gap

def row(cells):
    """cells: list of (text, width, align). Returns a spaced line."""
    return "".join(pad(t, w, a) for t, w, a in cells)

def table(headers, rows, aligns=None):
    """Render a standard, bordered, aligned ASCII table (CJK-aware widths).

    headers: list[str]; rows: list[list]; aligns: per-column 'left'/'right'.
    Columns auto-size to their widest cell so nothing ever wraps mid-row. This is
    the safe, readable replacement for the old 270-column mega-row: fixed grid,
    every number stays under its header, keyed left-to-right.
    """
    ncol = len(headers)
    aligns = aligns or ["left"] * ncol
    cells = [[str(c) for c in r] for r in rows]
    w = [display_width(h) for h in headers]
    for r in cells:
        for i in range(ncol):
            w[i] = max(w[i], display_width(r[i]))
    def rule(fill="-", j="+"):
        return j + j.join(fill * (wi + 2) for wi in w) + j
    def line(vals):
        return "| " + " | ".join(pad(vals[i], w[i], aligns[i])
                                 for i in range(ncol)) + " |"
    out = [rule(), line(headers), rule("=")]
    out += [line(r) for r in cells]
    out.append(rule())
    return "\n".join(out)

# ---------------------------------------------------------------- consensus
def consensus(prices, max_spread_pct=1.0):
    """Median + agreement across sources. prices: {source: value}."""
    vals = [v for v in prices.values() if v is not None]
    if not vals:
        return None
    med = statistics.median(vals)
    spread = (max(vals) - min(vals)) / med * 100 if med else 0.0
    return {"median": med, "n": len(vals), "spread_pct": round(spread, 3),
            "trusted": len(vals) >= 2 and spread <= max_spread_pct,
            "prices": prices}
