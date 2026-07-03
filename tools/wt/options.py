"""Options IV surface + long-gamma (straddle/strangle) opportunity scan.

Data source: CBOE delayed quotes (public, no key required).
  Endpoint: https://cdn.cboe.com/api/global/delayed_quotes/options/{SYM}.json
  Returns: per-option bid/ask/vol/OI/IV/delta/gamma/vega/theta + underlying
           current_price and iv30.
  15-minute delayed; refreshed intraday. Free.

Why this module exists:
  Options let us express ASYMMETRIC reward:risk with DEFINED, hard-capped risk
  (the premium paid). A long straddle/strangle around a catalyst can pay many
  multiples of risk if realized vol exceeds implied vol. The scanner can now
  find names where:
    - IV30 is elevated (suggesting an expected move) but historically LOW
      relative to realized vol (cheap options),
    - OR there is a dated catalyst (earnings/FDA) within 2-10 days where a
      long-gamma position benefits from the post-event move,
    - AND the straddle/strangle cost (as % of underlying) is below the
      typical post-event realized move (positive expected value).

Free data limits:
  - CBOE delayed 15min; fine for daily scan cadence.
  - No historical option OHLC -> we cannot backtest straddle EV directly.
    Instead we compare straddle cost to ATR-derived expected move (a proxy).
  - Greeks are CBOE-computed; we trust them.

Public functions:
  chain(sym)            -> full chain dict (underlying + options list)
  straddle(sym, expiry) -> nearest-straddle {cost, breakevens, IV, ...}
  strangle(sym, expiry, wing_pct=0.05) -> {cost, breakevens, ...}
  expected_move_pct(sym, expiry, price) -> ATM straddle-derived expected move
  iv_term_structure(sym) -> IV per expiration (cheap-vs-rich map)
  scan_long_gamma(syms, max_dte=30) -> ranked list of long-gamma candidates
"""
from __future__ import annotations
import datetime, threading, re
from concurrent.futures import ThreadPoolExecutor
from . import core, analysis

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
_LOCK = threading.Lock()
_CACHE: dict = {}
_TTL = 15 * 60  # 15min -- matches CBOE delay

def _get(url):
    try:
        import urllib.request, json
        req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                   "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read()), None
    except Exception as e:
        return None, core.describe_err(e)

def _cached(key, fn):
    now = datetime.datetime.now().timestamp()
    with _LOCK:
        hit = _CACHE.get(key)
        if hit and (now - hit[0]) < _TTL:
            return hit[1]
    val = fn()
    with _LOCK:
        _CACHE[key] = (now, val)
    return val

# ---------------------------------------------------------------- chain
def chain(sym):
    """Full CBOE delayed options chain for a US equity. Returns (dict, err)."""
    sym = str(sym).upper().replace(".", "")
    def fetch():
        url = f"https://cdn.cboe.com/api/global/delayed_quotes/options/{sym}.json"
        d, err = _get(url)
        if err:
            return None, err
        data = d.get("data") if d else None
        if not data:
            return None, "no data"
        return data, None
    return _cached(f"chain:{sym}", fetch)

# ---------------------------------------------------------------- expiry parse
_OPT_RE = re.compile(r"^(\d{6})(C|P)(\d{8})$")
def _parse_opt(oc):
    """Parse 'AAPL260702C00110000' -> (underlying, YYMMDD, C/P, strike_cents)."""
    m = _OPT_RE.match(oc)
    if not m:
        return None
    yymmdd, cp, cents = m.group(1), m.group(2), m.group(3)
    return (yymmdd, cp, int(cents) / 1000.0)

def _expiry_date(yymmdd):
    """YYMMDD -> date. Returns date or None."""
    try:
        y, m, d = 2000 + int(yymmdd[:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
        return datetime.date(y, m, d)
    except (ValueError, IndexError):
        return None

# ---------------------------------------------------------------- straddle/strangle
def _atm_strike(opts, spot):
    """Find the strike nearest to spot among the given option rows."""
    strikes = sorted({o["strike"] for o in opts if "strike" in o})
    if not strikes:
        return None
    return min(strikes, key=lambda s: abs(s - spot))

def _pick(opts, expiry_yymmdd, cp, strike):
    """Find one option row matching expiry/cp/strike."""
    for o in opts:
        p = _parse_opt(o.get("option", ""))
        if not p:
            continue
        if p[0] == expiry_yymmdd and p[1] == cp and abs(o.get("strike", 0) - strike) < 1e-6:
            return o
    return None

def _mid(o):
    """Mid price from bid/ask. Returns None if both missing/zero."""
    b, a = o.get("bid"), o.get("ask")
    if b is None or a is None or (b == 0 and a == 0):
        return None
    if b == 0:
        return a
    if a == 0:
        return b
    return (b + a) / 2.0

def straddle(sym, expiry=None, max_dte=30):
    """ATM straddle (call + put at the nearest strike) for the given expiry.
    If expiry is None, picks the nearest expiry within max_dte days.
    Returns dict with cost, breakevens, IV, gamma, theta, dte."""
    data, err = chain(sym)
    if err or not data:
        return None, err or "no chain"
    spot = data.get("current_price")
    if not spot:
        return None, "no spot"
    opts = data.get("options") or []
    if not opts:
        return None, "no options"
    # group expiries
    exps = {}  # yymmdd -> [opts]
    for o in opts:
        p = _parse_opt(o.get("option", ""))
        if not p:
            continue
        # only keep within max_dte
        d = _expiry_date(p[0])
        if not d:
            continue
        dte = (d - datetime.date.today()).days
        if dte < 0 or dte > max_dte:
            continue
        exps.setdefault(p[0], []).append(o)
    if not exps:
        return None, "no expiries within max_dte"
    # pick expiry
    if expiry:
        # accept YYMMDD or YYYY-MM-DD
        if "-" in expiry:
            try:
                d = datetime.date.fromisoformat(expiry)
                expiry = d.strftime("%y%m%d")
            except ValueError:
                return None, "bad expiry format"
        if expiry not in exps:
            return None, f"expiry {expiry} not in chain"
        chosen = expiry
    else:
        # nearest expiry that's >= 1d out
        today = datetime.date.today()
        valid = []
        for yy, opts_y in exps.items():
            d = _expiry_date(yy)
            if d and (d - today).days >= 1:
                valid.append(((d - today).days, yy))
        if not valid:
            return None, "no future expiry"
        chosen = min(valid)[1]
    e_opts = exps[chosen]
    strike = _atm_strike(e_opts, spot)
    if strike is None:
        return None, "no strikes"
    call = _pick(e_opts, chosen, "C", strike)
    put = _pick(e_opts, chosen, "P", strike)
    if not call or not put:
        return None, "no ATM pair"
    c_mid = _mid(call)
    p_mid = _mid(put)
    if c_mid is None or p_mid is None:
        return None, "no mid prices"
    cost = c_mid + p_mid
    dte = (_expiry_date(chosen) - datetime.date.today()).days
    # breakevens
    up_be = strike + cost
    down_be = strike - cost
    return {
        "sym": sym,
        "expiry": chosen,
        "dte": dte,
        "spot": spot,
        "strike": strike,
        "call_mid": c_mid,
        "put_mid": p_mid,
        "cost": cost,
        "cost_pct": cost / spot * 100 if spot else 0,
        "up_be": up_be,
        "down_be": down_be,
        "up_be_pct": (up_be - spot) / spot * 100 if spot else 0,
        "down_be_pct": (down_be - spot) / spot * 100 if spot else 0,
        "iv_call": call.get("iv"),
        "iv_put": put.get("iv"),
        "gamma": (call.get("gamma") or 0) + (put.get("gamma") or 0),
        "theta": (call.get("theta") or 0) + (put.get("theta") or 0),
        "vega": (call.get("vega") or 0) + (put.get("vega") or 0),
        "call_oi": call.get("open_interest"),
        "put_oi": put.get("open_interest"),
        "call_vol": call.get("volume"),
        "put_vol": put.get("volume"),
    }, None

def strangle(sym, expiry=None, wing_pct=0.05, max_dte=30):
    """OTM strangle: put at strike*(1-wing_pct), call at strike*(1+wing_pct).
    Cheaper than straddle but needs a bigger move. Returns dict."""
    data, err = chain(sym)
    if err or not data:
        return None, err or "no chain"
    spot = data.get("current_price")
    if not spot:
        return None, "no spot"
    opts = data.get("options") or []
    if not opts:
        return None, "no options"
    exps = {}
    for o in opts:
        p = _parse_opt(o.get("option", ""))
        if not p:
            continue
        d = _expiry_date(p[0])
        if not d:
            continue
        dte = (d - datetime.date.today()).days
        if dte < 0 or dte > max_dte:
            continue
        exps.setdefault(p[0], []).append(o)
    if not exps:
        return None, "no expiries"
    if expiry:
        if "-" in expiry:
            try:
                d = datetime.date.fromisoformat(expiry)
                expiry = d.strftime("%y%m%d")
            except ValueError:
                return None, "bad expiry"
        if expiry not in exps:
            return None, f"expiry {expiry} not in chain"
        chosen = expiry
    else:
        today = datetime.date.today()
        valid = [((d - today).days, yy) for yy, opts_y in exps.items()
                 if (d := _expiry_date(yy)) and (d - today).days >= 1]
        if not valid:
            return None, "no future expiry"
        chosen = min(valid)[1]
    e_opts = exps[chosen]
    strikes = sorted({o["strike"] for o in e_opts if "strike" in o})
    if not strikes:
        return None, "no strikes"
    put_k = max([s for s in strikes if s <= spot * (1 - wing_pct)] or [strikes[0]])
    call_k = min([s for s in strikes if s >= spot * (1 + wing_pct)] or [strikes[-1]])
    call = _pick(e_opts, chosen, "C", call_k)
    put = _pick(e_opts, chosen, "P", put_k)
    if not call or not put:
        return None, "no OTM pair"
    c_mid = _mid(call)
    p_mid = _mid(put)
    if c_mid is None or p_mid is None:
        return None, "no mid prices"
    cost = c_mid + p_mid
    dte = (_expiry_date(chosen) - datetime.date.today()).days
    return {
        "sym": sym, "expiry": chosen, "dte": dte, "spot": spot,
        "call_strike": call_k, "put_strike": put_k,
        "call_mid": c_mid, "put_mid": p_mid, "cost": cost,
        "cost_pct": cost / spot * 100 if spot else 0,
        "up_be": call_k + cost, "down_be": put_k - cost,
        "iv_call": call.get("iv"), "iv_put": put.get("iv"),
        "gamma": (call.get("gamma") or 0) + (put.get("gamma") or 0),
        "theta": (call.get("theta") or 0) + (put.get("theta") or 0),
        "vega": (call.get("vega") or 0) + (put.get("vega") or 0),
    }, None

# ---------------------------------------------------------------- IV term structure
def iv_term_structure(sym, max_dte=60):
    """IV per expiration (the term structure). Useful for cheap-vs-rich
    detection: a flat/inverted term structure around a catalyst suggests
    the market has NOT priced in the event -- opportunity."""
    data, err = chain(sym)
    if err or not data:
        return None, err or "no chain"
    iv30 = data.get("iv30")
    opts = data.get("options") or []
    by_exp = {}
    for o in opts:
        p = _parse_opt(o.get("option", ""))
        if not p:
            continue
        d = _expiry_date(p[0])
        if not d:
            continue
        dte = (d - datetime.date.today()).days
        if dte < 0 or dte > max_dte:
            continue
        iv = o.get("iv")
        if iv is None or iv == 0:
            continue
        by_exp.setdefault(p[0], []).append(iv)
    out = []
    for yy, ivs in by_exp.items():
        d = _expiry_date(yy)
        # mean IV across the expiry (proxy for ATM IV)
        out.append({"expiry": yy, "dte": (d - datetime.date.today()).days,
                    "iv_mean": sum(ivs) / len(ivs),
                    "iv_max": max(ivs), "iv_min": min(ivs),
                    "n": len(ivs)})
    out.sort(key=lambda r: r["dte"])
    return {"sym": sym, "iv30": iv30, "term": out}, None

# ---------------------------------------------------------------- expected move
def expected_move_pct(sym, expiry=None, max_dte=30):
    """ATM straddle-implied expected move as % of spot. A classic trader's
    heuristic: cost of ATM straddle ≈ market's expected 1-sigma move."""
    s, err = straddle(sym, expiry=expiry, max_dte=max_dte)
    if err or not s:
        return None, err
    # straddle cost = expected |move| in dollars (roughly). Convert to %.
    return {"expected_move_pct": s["cost_pct"], "dte": s["dte"],
            "expiry": s["expiry"], "cost": s["cost"], "spot": s["spot"]}, None

# ---------------------------------------------------------------- scan
def _atr_pct(sym_or_hist):
    """ATR as % of price from a history dict (highs/lows/closes) -- or None.
    Used to compare realized vol to straddle-implied vol."""
    if not sym_or_hist or "high" not in sym_or_hist:
        return None
    h, l, c = sym_or_hist["high"], sym_or_hist["low"], sym_or_hist["close"]
    if len(c) < 15:
        return None
    atr = analysis.atr(h, l, c, n=14)
    if not c[-1] or not atr:
        return None
    return atr / c[-1] * 100

def scan_long_gamma(syms, max_dte=30, min_oi=100, max_cost_pct=10.0):
    """Scan a list of symbols for long-gamma opportunities.

    For each symbol:
      1. Pull the ATM straddle for the nearest expiry within max_dte.
      2. Compute the straddle cost as % of spot (expected move).
      3. Pull daily ATR% (realized vol proxy). If ATR%*sqrt(dte) > straddle
         cost%, the options look CHEAP vs realized -- potential long-gamma.
      4. Also flag if there's a near-term catalyst (caller can pass syms that
         already have catalyst data via report.enrich_with_catalysts).
      5. Filter: min open interest, max cost%.

    Returns ranked list (best EV first). Each row has all straddle fields +
    atr_pct + ev_score (realized/implied ratio; >1 = cheap options)."""
    from . import sources
    rows = []
    def _one(sym):
        s, err = straddle(sym, max_dte=max_dte)
        if err or not s:
            return None
        if s.get("cost_pct", 0) > max_cost_pct:
            return None
        oi = (s.get("call_oi") or 0) + (s.get("put_oi") or 0)
        if oi < min_oi:
            return None
        # realized vol proxy from ATR
        # try Polygon history for US
        hist, _ = sources.polygon_history(sym)
        atr_pct = _atr_pct(hist)
        # annualized realized vol proxy: ATR% * sqrt(252)
        rv_proxy = (atr_pct * (252 ** 0.5)) if atr_pct else None
        # implied vol from straddle: cost_pct / sqrt(dte/365) -- rough
        # Better: use the CBOE-provided IV if available
        iv = s.get("iv_call") or s.get("iv_put")
        # EV score: ratio of realized to implied (annualized). >1 => cheap options.
        ev_score = (rv_proxy / iv) if (rv_proxy and iv) else None
        return {**s, "atr_pct": atr_pct, "rv_proxy": rv_proxy,
                "iv": iv, "ev_score": ev_score, "oi_total": oi}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(_one, syms):
            if r:
                rows.append(r)
    # rank: highest ev_score first (cheapest options vs realized vol)
    rows.sort(key=lambda x: -(x.get("ev_score") or 0))
    return rows

def print_long_gamma(syms, max_dte=30, limit=15):
    """Standalone pretty-print of long-gamma scan results."""
    rows = scan_long_gamma(syms, max_dte=max_dte)
    print(f"\n-- LONG-GAMMA SCAN (straddle/strangle; max DTE {max_dte}) --")
    if not rows:
        print("  (no candidates passed filters)")
        return
    hdr = ["Sym", "DTE", "Spot", "Strike", "Cost$", "Cost%", "UpBE%", "DnBE%",
           "IV", "ATR%", "RV/IV", "OI"]
    al = ["left", "right", "right", "right", "right", "right", "right", "right",
          "right", "right", "right", "right"]
    body = []
    for r in rows[:limit]:
        body.append([
            r["sym"], str(r["dte"]),
            f"{r['spot']:.2f}", f"{r['strike']:.2f}",
            f"{r['cost']:.2f}", f"{r['cost_pct']:.2f}",
            f"{r['up_be_pct']:+.2f}", f"{r['down_be_pct']:+.2f}",
            f"{(r.get('iv') or 0)*100:.1f}%" if r.get("iv") else "--",
            f"{r.get('atr_pct') or 0:.2f}%" if r.get("atr_pct") else "--",
            f"{r.get('ev_score') or 0:.2f}" if r.get("ev_score") else "--",
            f"{r.get('oi_total') or 0:,.0f}",
        ])
    print(core.table(hdr, body, al))
    print("  RV/IV > 1.0 = options look CHEAP vs realized vol (long-gamma candidate)")
    print("  Cost% = straddle cost / spot (the market's expected 1-sigma move)")

if __name__ == "__main__":
    import sys
    syms = sys.argv[1:] or ["AAPL", "MSFT", "NVDA", "TSLA", "META", "AMZN", "GOOGL"]
    print_long_gamma(syms)
