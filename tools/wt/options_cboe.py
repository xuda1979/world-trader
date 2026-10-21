"""CBOE delayed-quotes options chains -- keyless analytics (added 2026-09-07).

Free, no key, no scraping: cdn.cboe.com serves the full delayed option chain
(equities + indexes) as JSON with bid/ask, volume, open_interest, iv and
Greeks per contract. Replaces the Yahoo path that died (v8 chart 403s from
this host) and adds data the repo never had: put/call volume+OI, ATM IV,
25-delta skew -- per name and aggregate, for the scan and regime layers.

Contract grammar (OCC): ROOT + YYMMDD + C/P + strike*1000 (8 digits).
Index symbols (SPX, VIX, ...) are served under an underscore-prefixed file.
"""
from __future__ import annotations
import json
import re

from .core import get_json

CDN = "https://cdn.cboe.com/api/global/delayed_quotes/options"
INDEXES = {"SPX", "SPXW", "VIX", "NDX", "RUT", "DJX", "XSP", "VIX9D"}

_PAT = re.compile(r"^([A-Z.]+)([0-9]{6})([CP])([0-9]{8})$")


def parse_contract(sym):
    """OCC option symbol -> (root, yymmdd, C/P, strike). Raises on garbage."""
    m = _PAT.match(str(sym or "").strip())
    if not m:
        raise ValueError("bad option symbol: %r" % (sym,))
    return m.group(1), m.group(2), m.group(3), int(m.group(4)) / 1000.0


def chain_url(sym):
    """CBOE CDN URL for a symbol; indexes live under an underscore file."""
    if sym.upper() in INDEXES:
        return "%s/_%s.json" % (CDN, sym.upper())
    return "%s/%s.json" % (CDN, sym.upper())


def fetch_chain(sym, timeout=30):
    """Raw CBOE chain dict (data.options list) or raises."""
    return get_json(chain_url(sym), timeout=timeout)


def chain_analytics(options, spot=None):
    """Aggregate a parsed-options list into put/call, IV and skew stats.

    Fail-closed: raises ValueError on an empty chain or one with no
    parseable contract, so callers never mistake a dead feed for a signal.
    """
    parsed = []
    for o in options or []:
        try:
            root, exp, cp, strike = parse_contract(o.get("option"))
        except ValueError:
            continue
        o2 = dict(o)
        o2["_root"], o2["_exp"], o2["_cp"], o2["_strike"] = root, exp, cp, strike
        parsed.append(o2)
    if not parsed:
        raise ValueError("no parseable contracts in chain (%d rows)" % len(options or []))

    calls = [o for o in parsed if o["_cp"] == "C"]
    puts = [o for o in parsed if o["_cp"] == "P"]
    cv = sum(float(o.get("volume") or 0) for o in calls)
    pv = sum(float(o.get("volume") or 0) for o in puts)
    oic = sum(float(o.get("open_interest") or 0) for o in calls)
    oip = sum(float(o.get("open_interest") or 0) for o in puts)

    def _nearest_iv(contracts):
        if spot is None or not contracts:
            return None
        live = [o for o in contracts if (o.get("iv") or 0) > 0]
        if not live:
            return None
        return min(live, key=lambda o: abs(o["_strike"] - spot))["iv"]

    iv_call = _nearest_iv(calls)
    iv_put = _nearest_iv(puts)
    atm_iv = None
    if iv_call is not None and iv_put is not None:
        atm_iv = (iv_call + iv_put) / 2.0
    else:
        atm_iv = iv_call if iv_call is not None else iv_put

    def _iv_at_delta(contracts, target):
        if spot is None:
            return None
        live = [o for o in contracts
                if o.get("delta") is not None and (o.get("iv") or 0) > 0
                and abs(abs(float(o["delta"])) - target) <= 0.05]
        if not live:
            return None
        return min(live, key=lambda o: abs(abs(float(o["delta"])) - target))["iv"]

    skew = None
    c25 = _iv_at_delta(calls, 0.25)
    p25 = _iv_at_delta(puts, 0.25)
    if c25 is not None and p25 is not None:
        skew = p25 - c25

    return {
        "n_contracts": len(parsed),
        "total_volume": cv + pv,
        "total_oi": oic + oip,
        "call_volume": cv,
        "put_volume": pv,
        "pc_vol": pv / cv if cv > 0 else None,
        "pc_oi": oip / oic if oic > 0 else None,
        "atm_iv_call": iv_call,
        "atm_iv_put": iv_put,
        "atm_iv": atm_iv,
        "iv_atm_spread": (iv_put - iv_call) if (iv_call is not None and iv_put is not None) else None,
        "iv_25d_call": c25,
        "iv_25d_put": p25,
        "skew_25d": skew,
    }


def fetch_analytics(sym, timeout=30):
    """Fetch one chain from CBOE and return (analytics, spot) or raises."""
    d = fetch_chain(sym, timeout=timeout)
    data = d.get("data") or {}
    spot = data.get("current_price")
    return chain_analytics(data.get("options"), spot=spot), spot


def aggregate(symbols, fetch=None, timeout=30):
    """Roll up per-name analytics across many symbols, isolating failures.

    fetch(sym) -> chain options list; defaults to fetch_chain. Per-name
    errors land in the errors dict and never abort the sweep.
    """
    fetch = fetch or (lambda s: fetch_chain(s, timeout=timeout))
    per = {}
    errors = {}
    spots = {}
    for s in symbols:
        try:
            d = fetch(s)
            if isinstance(d, dict) and "data" in d:
                data = d.get("data") or {}
                opts = data.get("options")
                spot = data.get("current_price")
            elif isinstance(d, list):
                opts = d
                spot = None
            else:
                opts, spot = None, None
            if spot:
                spots[s] = spot
            per[s] = chain_analytics(opts, spot=spot)
        except Exception as e:
            errors[s] = str(e)[:200]
    ok = [per[s] for s in symbols if s in per]
    pcv = sorted(v["pc_vol"] for v in ok if v.get("pc_vol") is not None)
    return {
        "names": [s for s in symbols if s in per],
        "per_name": per,
        "spots": spots,
        "n_ok": len(per),
        "n_fail": len(errors),
        "errors": errors,
        "median_pc_vol": (pcv[len(pcv) // 2] if pcv else None),
        "breadth_pc_vol_gt1": sum(1 for v in ok if (v.get("pc_vol") or 0) > 1.0),
        "median_atm_iv": _median([v["atm_iv"] for v in ok if v.get("atm_iv") is not None]),
    }


def _median(xs):
    xs = sorted(xs)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2.0
