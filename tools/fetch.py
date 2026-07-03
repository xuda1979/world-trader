#!/usr/bin/env python3
"""Multi-source market-data fetcher for the trade-scout skill.

Pulls live quotes for equities, crypto, and FX from several free, public
endpoints, then cross-checks them so a single bad/stale source can't drive a
decision. Standard library only -- no pip install required.

Usage:
    python3 fetch.py crypto BTC ETH SOL
    python3 fetch.py equity AAPL MSFT
    python3 fetch.py fx USD EUR GBP JPY
    python3 fetch.py crypto BTC --json

Every source is best-effort: failures (timeout, block, JS challenge, schema
change) are caught per-source and reported, never fatal. A symbol is only
trusted when >=2 independent sources agree within MAX_SPREAD_PCT.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

TIMEOUT = 12  # seconds per HTTP request
UA = "Mozilla/5.0 (trade-scout fetcher; research only)"
# Spread above which sources are considered to disagree (consensus untrusted).
MAX_SPREAD_PCT = 1.0

# Crypto majors: symbol -> per-source identifiers.
CRYPTO_IDS = {
    "BTC": {"coingecko": "bitcoin", "kraken": "XBTUSD"},
    "ETH": {"coingecko": "ethereum", "kraken": "ETHUSD"},
    "SOL": {"coingecko": "solana", "kraken": "SOLUSD"},
    "XRP": {"coingecko": "ripple", "kraken": "XRPUSD"},
    "ADA": {"coingecko": "cardano", "kraken": "ADAUSD"},
    "DOGE": {"coingecko": "dogecoin", "kraken": "DOGEUSD"},
    "AVAX": {"coingecko": "avalanche-2", "kraken": "AVAXUSD"},
    "LINK": {"coingecko": "chainlink", "kraken": "LINKUSD"},
    "MATIC": {"coingecko": "matic-network", "kraken": "MATICUSD"},
    "LTC": {"coingecko": "litecoin", "kraken": "LTCUSD"},
}


@dataclass
class Quote:
    symbol: str
    price: float
    currency: str
    source: str
    asof: str  # ISO-8601 UTC


@dataclass
class SourceError:
    symbol: str
    source: str
    error: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get(url: str, *, parse_json: bool = True):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw) if parse_json else raw


# --- Crypto sources --------------------------------------------------------

def src_coinbase(sym: str) -> Quote:
    d = _get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot")
    return Quote(sym, float(d["data"]["amount"]), "USD", "coinbase", _now())


def src_binance(sym: str) -> Quote:
    d = _get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT")
    return Quote(sym, float(d["price"]), "USDT", "binance", _now())


def src_coingecko(sym: str) -> Quote:
    cid = CRYPTO_IDS.get(sym, {}).get("coingecko")
    if not cid:
        raise ValueError(f"no coingecko id mapped for {sym}")
    d = _get(f"https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies=usd")
    return Quote(sym, float(d[cid]["usd"]), "USD", "coingecko", _now())


def src_kraken(sym: str) -> Quote:
    pair = CRYPTO_IDS.get(sym, {}).get("kraken")
    if not pair:
        raise ValueError(f"no kraken pair mapped for {sym}")
    d = _get(f"https://api.kraken.com/0/public/Ticker?pair={pair}")
    if d.get("error"):
        raise ValueError("; ".join(d["error"]))
    result = next(iter(d["result"].values()))
    return Quote(sym, float(result["c"][0]), "USD", "kraken", _now())


def src_coincap(sym: str) -> Quote:
    cid = CRYPTO_IDS.get(sym, {}).get("coingecko")  # coincap reuses gecko-style ids
    if not cid:
        raise ValueError(f"no coincap id mapped for {sym}")
    d = _get(f"https://api.coincap.io/v2/assets/{cid}")
    return Quote(sym, float(d["data"]["priceUsd"]), "USD", "coincap", _now())


CRYPTO_SOURCES = [src_coinbase, src_binance, src_coingecko, src_kraken, src_coincap]


# --- Equity sources --------------------------------------------------------

def src_stooq(sym: str) -> Quote:
    raw = _get(f"https://stooq.com/q/l/?s={sym.lower()}.us&f=sd2t2ohlcv&h&e=csv",
               parse_json=False)
    lines = [ln for ln in raw.strip().splitlines() if ln]
    if len(lines) < 2 or "," not in lines[1]:
        raise ValueError("unexpected stooq response (challenge or empty)")
    cols = lines[1].split(",")
    # Symbol,Date,Time,Open,High,Low,Close,Volume
    close = cols[6]
    if close in ("", "N/D"):
        raise ValueError("stooq returned no close")
    return Quote(sym.upper(), float(close), "USD", "stooq", _now())


def src_yahoo(sym: str) -> Quote:
    d = _get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
             "?range=1d&interval=1d")
    res = d["chart"]["result"]
    if not res:
        raise ValueError(d.get("chart", {}).get("error") or "empty yahoo result")
    meta = res[0]["meta"]
    price = meta.get("regularMarketPrice")
    if price is None:
        raise ValueError("yahoo missing regularMarketPrice")
    return Quote(sym.upper(), float(price), meta.get("currency", "USD"),
                 "yahoo", _now())


EQUITY_SOURCES = [src_stooq, src_yahoo]


# --- FX --------------------------------------------------------------------

def fetch_fx(base: str, symbols: list[str]) -> tuple[list[Quote], list[SourceError]]:
    base = base.upper()
    syms = ",".join(s.upper() for s in symbols)
    quotes: list[Quote] = []
    errors: list[SourceError] = []
    try:
        d = _get(f"https://api.frankfurter.dev/v1/latest?base={base}&symbols={syms}")
        asof = d.get("date", _now())
        for cur, rate in d["rates"].items():
            quotes.append(Quote(f"{base}/{cur}", float(rate), cur, "frankfurter", asof))
    except Exception as e:  # noqa: BLE001 -- single FX source, report and move on
        errors.append(SourceError(f"{base}/{syms}", "frankfurter", _describe(e)))
    return quotes, errors


# --- Aggregation -----------------------------------------------------------

def _describe(e: Exception) -> str:
    if isinstance(e, urllib.error.HTTPError):
        return f"HTTP {e.code}"
    if isinstance(e, urllib.error.URLError):
        return f"network: {e.reason}"
    if isinstance(e, TimeoutError):
        return "timeout"
    return f"{type(e).__name__}: {e}"


def _fetch_one(source, sym: str):
    try:
        return source(sym), None
    except Exception as e:  # noqa: BLE001 -- per-source isolation is the point
        return None, SourceError(sym, source.__name__.replace("src_", ""), _describe(e))


def fetch_symbol(sym: str, sources) -> tuple[list[Quote], list[SourceError]]:
    quotes, errors = [], []
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        futs = [pool.submit(_fetch_one, s, sym) for s in sources]
        for f in as_completed(futs):
            q, err = f.result()
            (quotes if q else errors).append(q or err)
    return quotes, errors


def consensus(quotes: list[Quote]) -> dict | None:
    if not quotes:
        return None
    prices = [q.price for q in quotes]
    med = statistics.median(prices)
    spread_pct = (max(prices) - min(prices)) / med * 100 if med else 0.0
    return {
        "median": med,
        "n_sources": len(prices),
        "spread_pct": round(spread_pct, 4),
        "trusted": len(prices) >= 2 and spread_pct <= MAX_SPREAD_PCT,
        "prices": {q.source: q.price for q in quotes},
    }


# --- Reporting -------------------------------------------------------------

def report(kind: str, results: dict, as_json: bool) -> None:
    if as_json:
        out = {
            sym: {
                "quotes": [asdict(q) for q in r["quotes"]],
                "errors": [asdict(e) for e in r["errors"]],
                "consensus": r["consensus"],
            }
            for sym, r in results.items()
        }
        print(json.dumps(out, indent=2))
        return

    for sym, r in results.items():
        c = r["consensus"]
        if c is None:
            print(f"{sym:<10} NO DATA  (all sources failed)")
        else:
            flag = "ok" if c["trusted"] else "UNVERIFIED"
            print(f"{sym:<10} {c['median']:>14,.6g}  "
                  f"[{c['n_sources']} src, spread {c['spread_pct']}%]  {flag}")
            detail = "  ".join(f"{s}={p:g}" for s, p in c["prices"].items())
            print(f"           {detail}")
        for e in r["errors"]:
            print(f"           x {e.source}: {e.error}")
    print(f"\nfetched {_now()}  |  research only, verify before trading")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Multi-source market-data fetcher.")
    p.add_argument("kind", choices=["crypto", "equity", "fx"])
    p.add_argument("symbols", nargs="+",
                   help="tickers (crypto/equity) or 'BASE QUOTE...' for fx")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    args = p.parse_args(argv)

    results: dict = {}
    if args.kind == "fx":
        if len(args.symbols) < 2:
            p.error("fx needs a base and at least one quote currency, e.g. fx USD EUR")
        base, syms = args.symbols[0], args.symbols[1:]
        quotes, errors = fetch_fx(base, syms)
        per: dict = {q.symbol: {"quotes": [q], "errors": []} for q in quotes}
        for e in errors:
            per.setdefault(e.symbol, {"quotes": [], "errors": []})["errors"].append(e)
        for sym, r in per.items():
            r["consensus"] = consensus(r["quotes"])
        results = per
    else:
        sources = CRYPTO_SOURCES if args.kind == "crypto" else EQUITY_SOURCES
        for sym in args.symbols:
            quotes, errors = fetch_symbol(sym.upper(), sources)
            results[sym.upper()] = {
                "quotes": quotes,
                "errors": errors,
                "consensus": consensus(quotes),
            }

    report(args.kind, results, args.json)
    any_data = any(r["consensus"] for r in results.values())
    return 0 if any_data else 1


if __name__ == "__main__":
    sys.exit(main())
