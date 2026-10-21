"""Cross-exchange funding-rate differential scanner.

For each perp listed on multiple exchanges, find cases where one exchange
pays you to long and another charges you to short (or vice versa). This is
the cleanest funding arb: same underlying, opposite positions on two venues,
capture the funding-rate spread delta-neutrally.

Supported: Binance, Bybit, OKX, Gate, Bitget (public REST, no keys).

 Arb direction:
   funding_X > funding_Y by > threshold
   => SHORT perp on X (collect funding_X), LONG perp on Y (pay funding_Y)
   => net carry = funding_X - funding_Y per interval

Edge = (fr_high - fr_low) * projected_events - 2 * round_trip_fees.
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 15):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

# ---------- Per-exchange funding fetchers ----------
def binance_funding():
    """Returns {symbol: funding_rate_pct_8h} for all USDT perps."""
    rows = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    out = {}
    for r in rows:
        s = r.get("symbol", "")
        if not s.endswith("USDT"): continue
        try:
            out[s] = float(r.get("lastFundingRate", 0)) * 100  # %
        except (TypeError, ValueError):
            continue
    return out, "binance"

def bybit_funding():
    """Bybit V5 — funding is per-8h for most, but some are 4h or 1h."""
    d = _get("https://api.bybit.com/v5/market/tickers?category=linear")
    out = {}
    for t in d.get("result", {}).get("list", []):
        s = t.get("symbol", "")
        if not s.endswith("USDT"): continue
        fr = t.get("fundingRate")
        try:
            if fr is not None:
                out[s] = float(fr) * 100
        except (TypeError, ValueError):
            continue
    return out, "bybit"

def okx_funding():
    """OKX funding rates for SWAP instruments. Funding intervals vary."""
    out = {}
    # bulk endpoint
    d = _get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP")
    # OKX requires per-symbol call in this endpoint; fallback to all tickers
    try:
        # Actually OKX has /api/v5/public/instruments?instType=SWAP for the list,
        # then per-symbol funding. To keep this light we'll just hit a few majors
        # plus the all-swap tickers endpoint that includes funding.
        t = _get("https://www.okx.com/api/v5/public/tickers?instType=SWAP")
        for row in t.get("data", []):
            inst = row.get("instId", "")
            if not inst.endswith("-USDT-SWAP"): continue
            base = inst.replace("-USDT-SWAP", "") + "USDT"
            fr = row.get("fundingRate")
            try:
                if fr:
                    out[base] = float(fr) * 100
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return out, "okx"

def gate_funding():
    """Gate Futures funding rates."""
    out = {}
    try:
        d = _get("https://api.gateio.ws/api/v4/futures/usdt/contracts")
        for c in d:
            if not c.get("in_delisting"):
                s = c.get("name", "")
                if not s.endswith("_USDT"): continue
                base = s.replace("_USDT", "USDT")
                fr = c.get("funding_rate")
                try:
                    if fr is not None:
                        out[base] = float(fr) * 100
                except (TypeError, ValueError):
                    continue
    except Exception:
        pass
    return out, "gate"

def bitget_funding():
    """Bitget v2 funding rates."""
    out = {}
    try:
        d = _get("https://api.bitget.com/api/v2/market/tickers?productType=USDT-FUTURES")
        for row in d.get("data", []):
            s = row.get("symbol", "")
            if not s.endswith("USDT"): continue
            fr = row.get("fundingRate")
            try:
                if fr is not None:
                    out[s] = float(fr) * 100
            except (TypeError, ValueError):
                continue
    except Exception:
        pass
    return out, "bitget"

EXCHANGES = [binance_funding, bybit_funding, okx_funding, gate_funding, bitget_funding]

def scan(
    min_volume_m: float = 30.0,             # require $30M 24h volume on at least one venue
    min_spread_pct_8h: float = 0.03,        # 0.03% per 8h spread = ~33% APR gross
    fee_per_side_pct: float = 0.04,         # average maker+taker per side
    projected_events: int = 3,
    top_n: int = 25,
):
    """Find cross-exchange funding spreads.

    For each perp on >=2 exchanges, compute funding_high - funding_low.
    Edge = (funding_high - funding_low) * events - fees.
    Direction: SHORT high, LONG low.
    """
    # gather
    per_ex = {}
    for fetcher in EXCHANGES:
        try:
            rates, ex_id = fetcher()
            per_ex[ex_id] = rates
        except Exception as e:
            per_ex[getattr(fetcher, "__name__", "?")] = {}
            continue

    # intersect symbols across exchanges
    all_syms = set()
    for rates in per_ex.values():
        all_syms.update(rates.keys())

    cands = []
    for sym in all_syms:
        venues = {ex: r[sym] for ex, r in per_ex.items() if sym in r}
        if len(venues) < 2: continue
        hi_ex, hi_fr = max(venues.items(), key=lambda x: x[1])
        lo_ex, lo_fr = min(venues.items(), key=lambda x: x[1])
        spread = hi_fr - lo_fr
        if spread < min_spread_pct_8h: continue
        # fees: entry + exit, both venues
        fees = 4 * fee_per_side_pct  # 2 venues * (entry+exit) per venue
        net_pct = spread * projected_events - fees
        if net_pct <= 0: continue
        cands.append({
            "symbol": sym, "high_ex": hi_ex, "high_fr": hi_fr,
            "low_ex": lo_ex, "low_fr": lo_fr, "spread_pct_8h": spread,
            "fees_pct": fees, "net_pct_24h": net_pct,
            "apr_pct": net_pct / projected_events * 365,
            "venues": list(venues.keys()),
        })

    cands.sort(key=lambda x: x["net_pct_24h"], reverse=True)
    return cands[:top_n], per_ex

def print_table(rows, per_ex):
    print(f"  exchanges sampled: {sorted(per_ex.keys())} (rates per exchange: " +
          ", ".join(f"{e}={len(r)}" for e, r in per_ex.items()) + ")")
    if not rows:
        print("  no cross-exchange funding spread cleared the bar.")
        return
    hdr = ["Sym", "HighEx", "HighFR%", "LowEx", "LowFR%", "Spread%/8h", "Fees%", "Net%/24h", "APR%"]
    al = ["<", "<", ">", "<", ">", ">", ">", ">", ">"]
    widths = [12, 8, 9, 8, 9, 11, 7, 10, 8]
    sep = "  "
    def fmt_row(vals): return sep.join(str(v).rjust(widths[i]) for i, v in enumerate(vals))
    print("  " + fmt_row(hdr))
    print("  " + sep.join("-" * w for w in widths))
    for r in rows:
        print("  " + fmt_row([
            r["symbol"], r["high_ex"], f"{r['high_fr']:+.4f}",
            r["low_ex"], f"{r['low_fr']:+.4f}",
            f"{r['spread_pct_8h']:+.4f}", f"{r['fees_pct']:.3f}",
            f"{r['net_pct_24h']:+.3f}", f"{r['apr_pct']:+.1f}",
        ]))
    print("\n  Direction: SHORT on HighEx (collect), LONG on LowEx (pay). Net delta = 0.")
    print("  Verify funding intervals differ between exchanges (some are 4h vs 8h).")

if __name__ == "__main__":
    rows, per_ex = scan()
    print(f"=== CROSS-EXCHANGE FUNDING SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows, per_ex)
