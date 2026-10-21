"""Real-data history subsystem for the quant backtest engine.

The problem this solves
-----------------------
Up to 2026-07-22 the only backtests we had were on synthetic data (GBM, OU,
jump-diffusion).  The RV mean-reversion backtest reported Sharpe +6/+24/+34
on synthetic OU spreads -- those numbers describe the *model*, not the
market, so they are not evidence of an edge.  This module is the first
piece of a real-data pipeline: given a list of tickers, fetch daily OHLC
history from whatever provider will talk to us, cache it to CSV so we
don't re-fetch (and so flaky-network retries don't lose progress), and
return it in the same `{date,open,high,low,close,vol}` dict shape that
`tools.wt.analysis` and `tools.quant.backtest` already consume.

Providers (in priority order):
  * Polygon  -- US equities & ETFs (needs POLYGON_KEY, ~500 bars/call)
  * Binance  -- crypto 24/7 (no key, 400 bars/call for 1d)
  * Twelve Data -- FX/indices/equities fallback (needs TWELVEDATA_KEY,
                   rate-limited 8/min on free tier)
  * Stooq    -- CSV no-key fallback (often blocked on this network but
                included for completeness)

Cache layout
------------
    tools/quant/data/<provider>/<symbol>.csv
        columns: date,open,high,low,close,vol
        sorted oldest-first, header row included

A cache hit is returned instantly without any network call.  A cache miss
falls through to the providers; on success the file is written so the next
caller sees a hit.  Cache files are NEVER auto-invalidated -- callers who
want fresh data pass `refresh=True`.
"""

from __future__ import annotations
import os, sys, csv, time, json, datetime
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from tools.wt import sources
from tools.wt.core import http_get, get_json, api_key, describe_err

CACHE_DIR = os.path.join(ROOT, "tools", "quant", "data")


# ---------------------------------------------------------------- providers
def _try_polygon(sym: str, days: int) -> Tuple[Optional[Dict], Optional[str]]:
    """Polygon daily aggregates.  Free tier allows 5 calls/min, 500 bars/call."""
    if not api_key("POLYGON_KEY"):
        return None, "no key"
    # Polygon's `limit` caps at 50,000 but the free tier returns ~500 trading
    # days.  We ask for 2 years of history which is plenty for RV
    # mean-reversion work.
    start = (datetime.date.today() - datetime.timedelta(days=int(days * 1.5) + 10)).isoformat()
    return sources.polygon_history(sym, start=start, limit=min(days, 1000))


def _try_binance(sym: str, days: int) -> Tuple[Optional[Dict], Optional[str]]:
    """Binance daily klines for crypto.  No key needed.

    Normalizes the Binance openTime (epoch ms) to a YYYY-MM-DD date string
    so every provider returns the same shape.
    """
    hist, err = sources.binance_klines(sym, interval="1d", limit=min(days, 1000))
    if not hist:
        return None, err
    # convert epoch-ms -> YYYY-MM-DD (UTC, since Binance bars are UTC midnight)
    out_dates = []
    for d in hist["date"]:
        try:
            ts = int(d) / 1000.0
            out_dates.append(datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime("%Y-%m-%d"))
        except (ValueError, TypeError):
            # already a date string?
            out_dates.append(str(d))
    hist["date"] = out_dates
    return hist, None


def _try_twelvedata(sym: str, days: int) -> Tuple[Optional[Dict], Optional[str]]:
    """Twelve Data daily.  Free tier: 8 calls/min, 5000 bars/call."""
    return sources.twelvedata_history(sym, days=days)


def _try_stooq(sym: str, days: int) -> Tuple[Optional[Dict], Optional[str]]:
    """Stooq CSV (no key).  Often blocked on this network but try anyway."""
    return sources.stooq_history(sym, days=days)


# provider ordering per asset class
_PROVIDERS_US   = [_try_polygon, _try_twelvedata, _try_stooq]
_PROVIDERS_CRYPTO = [_try_binance]
_PROVIDERS_FX   = [_try_twelvedata, _try_stooq]


_CRYPTO_BASES = {"BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX",
                 "DOT", "MATIC", "LINK", "LTC", "UNI", "ATOM", "ARB", "OP",
                 "NEAR", "APT", "FIL", "INJ", "TIA", "SEI", "SUI", "RUNE"}


def _providers_for(sym: str) -> List:
    s = sym.upper()
    # explicit crypto pair (quote suffix)
    if s.endswith(("USDT", "BUSD", "USDC", "FDUSD", "TUSD")):
        return _PROVIDERS_CRYPTO
    # explicit crypto base (e.g. "BTC", "ETH") -- treat as <BASE>USDT
    if s in _CRYPTO_BASES:
        return _PROVIDERS_CRYPTO
    # crypto-crypto pair with hyphen e.g. "BTC-ETH"
    if "-" in s and s.split("-")[0] in _CRYPTO_BASES:
        return _PROVIDERS_CRYPTO
    # FX pair (contains "/" or is a 6-letter currency pair)
    if "/" in s:
        return _PROVIDERS_FX
    if len(s) == 6 and s[:3] in {"USD", "EUR", "GBP", "JPY", "AUD", "CAD",
                                  "CHF", "NZD", "CNY", "HKD", "SGD", "INR"}:
        return _PROVIDERS_FX
    return _PROVIDERS_US


# ---------------------------------------------------------------- cache
def _cache_path(provider: str, sym: str) -> str:
    safe = sym.replace("/", "_").replace(" ", "_").upper()
    return os.path.join(CACHE_DIR, provider, f"{safe}.csv")


def _read_cache(provider: str, sym: str) -> Optional[Dict]:
    p = _cache_path(provider, sym)
    if not os.path.exists(p):
        return None
    D, O, H, L, C, V = [], [], [], [], [], []
    try:
        with open(p, newline="") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                try:
                    D.append(row["date"])
                    O.append(float(row["open"]))
                    H.append(float(row["high"]))
                    L.append(float(row["low"]))
                    C.append(float(row["close"]))
                    V.append(float(row.get("vol") or 0.0))
                except (KeyError, ValueError):
                    continue
    except Exception:
        return None
    if len(C) < 20:
        return None
    return {"date": D, "open": O, "high": H, "low": L, "close": C, "vol": V,
            "_provider": provider, "_cached": True}


def _write_cache(provider: str, sym: str, hist: Dict) -> None:
    p = _cache_path(provider, sym)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    n = len(hist["close"])
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "vol"])
        for i in range(n):
            w.writerow([
                hist["date"][i],
                f"{hist['open'][i]:.6g}",
                f"{hist['high'][i]:.6g}",
                f"{hist['low'][i]:.6g}",
                f"{hist['close'][i]:.6g}",
                f"{(hist.get('vol') or [0]*n)[i]:.6g}",
            ])


# ---------------------------------------------------------------- public API
def fetch_history(sym: str, days: int = 500, refresh: bool = False,
                  retries: int = 3, retry_sleep: float = 2.0) -> Tuple[Optional[Dict], Optional[str]]:
    """Fetch daily OHLC for `sym` with provider fallback + CSV cache.

    Returns (hist_dict, err).  hist_dict has keys:
        date, open, high, low, close, vol, _provider, _cached
    oldest-first.  On a cache hit (refresh=False, file exists) we return
    immediately with no network call.
    """
    # 1) cache
    if not refresh:
        for prov in _providers_for(sym):
            cached = _read_cache(prov.__name__.replace("_try_", ""), sym)
            if cached:
                return cached, None
    # 2) live fetch with retries + provider fallback
    last_err = "no provider"
    for attempt in range(retries):
        for prov in _providers_for(sym):
            name = prov.__name__.replace("_try_", "")
            try:
                hist, err = prov(sym, days)
            except Exception as e:
                hist, err = None, describe_err(e)
            if hist and len(hist.get("close", [])) >= 20:
                _write_cache(name, sym, hist)
                hist["_provider"] = name
                hist["_cached"] = False
                return hist, None
            last_err = f"{name}: {err}"
        if attempt < retries - 1:
            time.sleep(retry_sleep)
    return None, last_err


def fetch_many(syms: List[str], days: int = 500, refresh: bool = False,
               workers: int = 6) -> Dict[str, Tuple[Optional[Dict], Optional[str]]]:
    """Parallel fetch over many symbols.  Returns {sym: (hist, err)}."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    out: Dict[str, Tuple[Optional[Dict], Optional[str]]] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(fetch_history, s, days, refresh): s for s in syms}
        for fut in as_completed(futs):
            s = futs[fut]
            try:
                out[s] = fut.result()
            except Exception as e:
                out[s] = (None, describe_err(e))
    return out


# ---------------------------------------------------------------- pairs
def fetch_pair(spread_sym: str, days: int = 500, refresh: bool = False
               ) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
    """Fetch two legs of a pair for RV / pairs-trading work.

    `spread_sym` is "LEG1/LEG2" e.g. "SPY/QQQ" or "BTC/ETH".
    Both legs are aligned to the COMMON date set (intersection) so the
    spread is well-defined on every bar.
    """
    a, b = spread_sym.split("/", 1)
    ha, ea = fetch_history(a.strip(), days=days, refresh=refresh)
    hb, eb = fetch_history(b.strip(), days=days, refresh=refresh)
    if not ha:
        return None, None, f"leg1 {a}: {ea}"
    if not hb:
        return None, None, f"leg2 {b}: {eb}"
    # align to common dates
    da = {d: i for i, d in enumerate(ha["date"])}
    db = {d: i for i, d in enumerate(hb["date"])}
    common = sorted(set(da) & set(db))
    if len(common) < 30:
        return None, None, f"too few common dates ({len(common)})"
    def pick(h, idx_map):
        idx = [idx_map[d] for d in common]
        return {
            "date": common,
            "open":   [h["open"][i] for i in idx],
            "high":   [h["high"][i] for i in idx],
            "low":    [h["low"][i] for i in idx],
            "close":  [h["close"][i] for i in idx],
            "vol":    [h["vol"][i] for i in idx],
            "_provider": h.get("_provider", "?"),
            "_cached":   h.get("_cached", False),
        }
    return pick(ha, da), pick(hb, db), None


def log_spread(a: Dict, b: Dict, w_a: float = 1.0, w_b: float = -1.0) -> Dict:
    """Construct a log-spread series from two aligned price dicts.

    spread_t = w_a * log(P_a) + w_b * log(P_b)

    The weights are *not* OLS hedge ratios -- they're caller-supplied so
    the caller can decide what "fair value" means (e.g. OLS beta, or
    equal-dollar, or 1:1 for a synthetic where both legs are indices).
    The OU half-life is computed on this spread by `backtest.run_rv_mean_reversion`.
    """
    import math
    n = len(a["close"])
    sa = [math.log(a["close"][i]) for i in range(n) if a["close"][i] > 0]
    sb = [math.log(b["close"][i]) for i in range(n) if b["close"][i] > 0]
    m = min(len(sa), len(sb))
    sa, sb = sa[-m:], sb[-m:]
    spread = [w_a * sa[i] + w_b * sb[i] for i in range(m)]
    return {"close": spread, "date": a["date"][-m:], "vol": [0.0]*m,
            "open": spread, "high": spread, "low": spread}


# ---------------------------------------------------------------- CLI
def _cli():
    import argparse
    ap = argparse.ArgumentParser(description="Fetch/cache daily OHLC history")
    ap.add_argument("symbols", nargs="*", help="e.g. SPY QQQ BTC ETHUSDT")
    ap.add_argument("--days", type=int, default=500)
    ap.add_argument("--refresh", action="store_true", help="bypass cache")
    ap.add_argument("--list", action="store_true", help="list cache contents")
    args = ap.parse_args()

    if args.list:
        if not os.path.isdir(CACHE_DIR):
            print("(no cache)")
            return 0
        for prov in sorted(os.listdir(CACHE_DIR)):
            d = os.path.join(CACHE_DIR, prov)
            if not os.path.isdir(d):
                continue
            files = sorted(os.listdir(d))
            print(f"{prov}/  ({len(files)} symbols)")
            for f in files[:20]:
                print(f"  {f}")
            if len(files) > 20:
                print(f"  ... +{len(files)-20} more")
        return 0

    for s in args.symbols:
        t0 = time.time()
        h, err = fetch_history(s, days=args.days, refresh=args.refresh)
        dt = time.time() - t0
        if h:
            prov = h.get("_provider", "?")
            cached = h.get("_cached", False)
            print(f"{s:12s} OK  {len(h['close']):4d} bars  "
                  f"via {prov:9s} {'(cache)' if cached else f'({dt:.1f}s)'}  "
                  f"last={h['close'][-1]:.4f}  date={h['date'][-1]}")
        else:
            print(f"{s:12s} FAIL  {err}  ({dt:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
