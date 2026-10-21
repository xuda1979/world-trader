"""Options RV vs IV edge scanner (revived 2026-09-07).

For each liquid optionable symbol, compare 20-day realized vol of the
underlying against ATM implied vol from CBOE delayed chains. RV > IV
beyond spread+fees => long-gamma straddle is statistically +EV; IV >> RV
=> short-vol (iron condor) is +EV.

Revival notes (the old version was silently dead):
  - Spot + iv30 come from the CBOE payload itself (data.current_price /
    data.iv30) — the dead Yahoo history leg is gone entirely.
  - Realized vol uses wt.sources.nasdaq_history() (keyless, works here).
  - The old parser read option_type/strike/expiration_date keys the CBOE
    payload never has; they are packed in the OCC contract symbol.
  - Unit trap: per-contract "iv" is DECIMAL, data-level "iv30" is PERCENT.
  - scan() never raises; failures skip that symbol.

TDD: tools/quant/data/cboe_options/test_options_rviv_revival.py
"""
from __future__ import annotations
import datetime as dt
import json, math, re, time, urllib.request

UA = dict([("User-Agent", "Mozilla/5.0 (research; world-trader)")])
CBOE_OPTIONS_URL = ("https://cdn.cboe.com/api/global/"
                    "delayed_quotes/options/%s.json")
OCC_RE = re.compile(r"^([A-Z]+)(\d{2})(\d{2})(\d{2})([CP])(\d{8})$")

DEFAULT_SYMBOLS = ["AAPL", "MSFT", "NVDA", "TSLA", "META", "AMZN", "GOOGL",
                   "AMD", "NFLX", "SPY", "QQQ", "IWM", "GLD", "SLV", "TLT",
                   "XLF", "XLE", "HYG", "USO"]

# Coverage of the last scan(): symbols requested / with chain / with RV /
# emitted. "No edge" is only honest when evaluated ~= requested.
LAST_SCAN_STATS = dict([("requested", 0), ("got_chain", 0), ("got_rv", 0),
                        ("evaluated", 0), ("emitted", 0), ("errors", [])])


def _f(v):
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _occ_parse(s):
    """OCC contract symbol -> (exp_iso, 'C'|'P', strike) or None."""
    if not isinstance(s, str):
        return None
    m = OCC_RE.match(s)
    if not m:
        return None
    root, yy, mm, dd, typ, k8 = m.groups()
    try:
        exp = dt.date(2000 + int(yy), int(mm), int(dd)).isoformat()
    except ValueError:
        return None
    return root, exp, typ, int(k8) / 1000.0


def _get(url, timeout=15.0):
    req = urllib.request.Request(url)
    for k, v in UA.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _fetch_cboe(sym, retries=1):
    """CBOE delayed chain -> (dict(symbol, spot, iv30, options), err)."""
    last = None
    for attempt in range(retries + 1):
        try:
            d = _get(CBOE_OPTIONS_URL % sym)
            data = d.get("data") or dict()
            spot = _f(data.get("current_price"))
            if not spot:
                return None, "no-spot-in-payload"
            return dict([("symbol", sym), ("spot", spot),
                         ("iv30", _f(data.get("iv30"))),
                         ("options", data.get("options") or [])]), None
        except Exception as e:
            last = e
            time.sleep(1)
    return None, repr(last)[:200]


def _load_nasdaq_history():
    """Resolve wt.sources.nasdaq_history under any launch mode.

    `python3 tools/wt/options_rviv.py` runs the file as a top-level module
    with tools/wt first on sys.path, so `wt` is not importable — bootstrap
    the repo tools/ dir (parent of this file's dir) onto sys.path and
    retry. (Bare `from sources import ...` can never work: sources.py
    itself uses relative imports, i.e. it is package-only.)
    """
    try:
        from wt.sources import nasdaq_history
        return nasdaq_history
    except ImportError:
        pass
    import os, sys
    tools_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.isdir(os.path.join(tools_dir, "wt")) and tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        from wt.sources import nasdaq_history
        return nasdaq_history
    except ImportError:
        return None


def _underlying_closes(sym, days=90):
    """Daily closes for the RV leg. Nasdaq, keyless (was: dead Yahoo)."""
    try:
        nasdaq_history = _load_nasdaq_history()
        if nasdaq_history is None:
            return []
        h, err = nasdaq_history(sym, days=days)
        if err or not h:
            return []
        return [c for c in (h.get("close") or []) if c is not None]
    except Exception:
        return []


def realized_vol(closes, window=20):
    """Annualized realized vol (%) from the last `window` daily returns."""
    if len(closes) < window + 1:
        return 0.0
    rets = []
    for i in range(len(closes) - window, len(closes)):
        if closes[i] > 0 and closes[i - 1] > 0:
            rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 5:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252.0) * 100.0


def atm_metrics(options, spot, iv30_pct=None, today=None):
    """Nearest expiry 7..45 DTE, strike closest to spot with both a call
    and a put (IV required). Returns dict or None. iv30_pct in percent."""
    if not spot or spot <= 0:
        return None
    today = today or dt.date.today()
    by_key = dict()
    for o in options or []:
        parsed = _occ_parse(o.get("option"))
        if not parsed:
            continue
        root, exp, typ, strike = parsed
        try:
            dte = (dt.date.fromisoformat(exp) - today).days
        except ValueError:
            continue
        if not (7 <= dte <= 45):
            continue
        by_key.setdefault((exp, strike), dict())[typ] = dict([
            ("bid", _f(o.get("bid"))), ("ask", _f(o.get("ask"))),
            ("iv", _f(o.get("iv"))), ("dte", dte)])
    best, best_score = None, None
    for (exp, strike), pair in by_key.items():
        c, p = pair.get("C"), pair.get("P")
        if not c or not p or c["iv"] is None or p["iv"] is None:
            continue
        straddle_mid = None
        if None not in (c["bid"], c["ask"], p["bid"], p["ask"]):
            straddle_mid = 0.5 * (c["bid"] + c["ask"]) + 0.5 * (p["bid"] + p["ask"])
        atm_iv = 0.5 * (c["iv"] + p["iv"]) * 100.0   # decimal -> percent
        score = abs(strike - spot) + 0.25 * pair["C"]["dte"]
        cand = dict([("exp", exp), ("atm_strike", strike),
                     ("atm_iv_pct", atm_iv), ("straddle_mid", straddle_mid),
                     ("dte", pair["C"]["dte"])])
        if best_score is None or score < best_score:
            best, best_score = cand, score
    if best is None:
        return None
    best["spot"] = spot
    best["iv30_pct"] = iv30_pct or 0.0
    return best


def scan(symbols=None, min_edge_pct=5.0, days=90):
    """RV vs IV edge per symbol, never raises. Sorted by |edge| desc."""
    if symbols is None:
        symbols = DEFAULT_SYMBOLS
    rows = []
    stats = dict([("requested", len(symbols)), ("got_chain", 0),
                  ("got_rv", 0), ("evaluated", 0), ("emitted", 0),
                  ("errors", [])])
    for sym in symbols:
        try:
            data, err = _fetch_cboe(sym)
            if err or not data:
                stats["errors"].append("%s:%s" % (sym, str(err)[:40]))
                continue
            stats["got_chain"] += 1
            closes = _underlying_closes(sym, days=days)
            rv = realized_vol(closes, window=20)
            if rv <= 0:
                stats["errors"].append("%s:no-rv" % sym)
                continue
            stats["got_rv"] += 1
            m = atm_metrics(data["options"], data["spot"],
                            data["iv30"], today=dt.date.today())
            if not m or m["atm_iv_pct"] <= 0:
                stats["errors"].append("%s:no-atm-pair" % sym)
                continue
            stats["evaluated"] += 1
            iv = m["atm_iv_pct"]
            edge = rv - iv
            if abs(edge) < min_edge_pct:
                continue
            straddle_cost = m["straddle_mid"] or 0.0
            rows.append(dict([
                ("symbol", sym), ("rv_pct", rv), ("iv_pct", iv),
                ("edge_pct", edge), ("straddle_cost", straddle_cost),
                ("straddle_pct", (straddle_cost / spot_guard(m)) * 100.0),
                ("spot", m["spot"]), ("exp", m["exp"]), ("dte", m["dte"]),
                ("atm_strike", m["atm_strike"]),
                ("iv30_pct", m["iv30_pct"]),
                ("trade", "long_gamma_straddle" if edge > 0 else "short_vol_iron_condor"),
            ]))
        except Exception:
            continue
    stats["emitted"] = len(rows)
    global LAST_SCAN_STATS
    LAST_SCAN_STATS = stats
    rows.sort(key=lambda x: abs(x["edge_pct"]), reverse=True)
    return rows


def spot_guard(m):
    s = m.get("spot") or 0.0
    return s if s > 0 else 1.0


def print_table(rows):
    s = LAST_SCAN_STATS
    if s["evaluated"]:
        print("  coverage: %d/%d symbols evaluated (%d chain-fail, %d no-RV, %d no-ATM)"
              % (s["evaluated"], s["requested"],
                 s["requested"] - s["got_chain"],
                 s["got_chain"] - s["got_rv"],
                 s["got_rv"] - s["evaluated"]))
    if not rows:
        print("  No RV/IV edge >= 5 vol points detected.")
        return
    print("%-6s %7s %7s %7s %10s %6s %9s %5s %8s  %s" % ("Sym", "RV%", "IV%",
        "Edge", "Straddle$", "Str%", "Spot", "DTE", "Exp", "Trade"))
    for r in rows:
        print("%-6s %7.2f %7.2f %+7.2f %10.2f %6.2f %9.2f %5d %8s  %s" % (
            r["symbol"], r["rv_pct"], r["iv_pct"], r["edge_pct"],
            r["straddle_cost"], r["straddle_pct"], r["spot"], r["dte"],
            r["exp"], r["trade"]))
    print("\n  Edge > +5 => long gamma (RV > IV, options cheap)")
    print("  Edge < -5 => short vol (IV > RV, premium rich)")


if __name__ == "__main__":
    rows = scan()
    print("=== OPTIONS RV/IV EDGE %s ===" % time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    print_table(rows)
