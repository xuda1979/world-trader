"""Triangular arbitrage within a single exchange.

Detects cycles like BTC -> ETH -> USDT -> BTC where the product of
three exchange rates > 1 (after fees). Real edge during volatility spikes
when one leg's order book is stale relative to the others.

Cycle types (on Binance USDT spot):
  USDT -> BTC -> ETH -> USDT  (start with USDT, end with USDT)
  USDT -> ETH -> BTC -> USDT
  USDT -> SOL -> BTC -> USDT  (and many other combos)

This scanner walks REAL L2 order book depth and only reports cycles that
survive taker fees at the available depth.
"""
from __future__ import annotations
import urllib.request, json, time
from itertools import permutations

UA = {"User-Agent": "curl/8"}
TAKER_FEE_PCT = 0.10  # Binance spot taker

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def book(sym: str, limit: int = 20):
    """Binance spot order book."""
    d = _get(f"https://api.binance.com/api/v3/depth?symbol={sym}&limit={limit}")
    return {
        "bids": [(float(p), float(q)) for p, q in d.get("bids", [])],
        "asks": [(float(p), float(q)) for p, q in d.get("asks", [])],
    }

def _consume(side: list[tuple[float, float]], quote_usdt: float) -> tuple[float, str | None]:
    """Walk asks to spend `quote_usdt` USDT. Return (base_qty_bought, None) or (0, reason)."""
    remaining = quote_usdt
    bought = 0.0
    for price, qty in side:
        cost = price * qty
        if cost >= remaining:
            take = remaining / price
            bought += take
            remaining = 0
            return bought, None
        bought += qty
        remaining -= cost
    return 0.0, "insufficient depth"

def _sell(side: list[tuple[float, float]], base_qty: float) -> tuple[float, str | None]:
    """Walk bids to sell `base_qty`. Return (usdt_received, None) or (0, reason)."""
    remaining = base_qty
    proceeds = 0.0
    for price, qty in side:
        if qty >= remaining:
            proceeds += price * remaining
            remaining = 0
            return proceeds, None
        proceeds += price * qty
        remaining -= qty
    return 0.0, "insufficient depth"

def _pair(from_coin: str, to_coin: str) -> str | None:
    """Binance spot symbol for from_coin -> to_coin (price = to_coin per from_coin)."""
    # Standard pair conventions
    if from_coin == "BTC" and to_coin == "USDT": return "BTCUSDT"
    if from_coin == "USDT" and to_coin == "BTC": return "BTCUSDT"
    if from_coin == "ETH" and to_coin == "USDT": return "ETHUSDT"
    if from_coin == "USDT" and to_coin == "ETH": return "ETHUSDT"
    if from_coin == "ETH" and to_coin == "BTC": return "ETHBTC"
    if from_coin == "BTC" and to_coin == "ETH": return "ETHBTC"
    if from_coin == "SOL" and to_coin == "USDT": return "SOLUSDT"
    if from_coin == "USDT" and to_coin == "SOL": return "SOLUSDT"
    if from_coin == "SOL" and to_coin == "BTC": return "SOLBTC"
    if from_coin == "BTC" and to_coin == "SOL": return "SOLBTC"
    if from_coin == "BNB" and to_coin == "USDT": return "BNBUSDT"
    if from_coin == "USDT" and to_coin == "BNB": return "BNBUSDT"
    if from_coin == "BNB" and to_coin == "BTC": return "BNBBTC"
    if from_coin == "BTC" and to_coin == "BNB": return "BNBBTC"
    if from_coin == "XRP" and to_coin == "USDT": return "XRPUSDT"
    if from_coin == "USDT" and to_coin == "XRP": return "XRPUSDT"
    if from_coin == "XRP" and to_coin == "BTC": return "XRPBTC"
    if from_coin == "BTC" and to_coin == "XRP": return "XRPBTC"
    if from_coin == "ADA" and to_coin == "USDT": return "ADAUSDT"
    if from_coin == "USDT" and to_coin == "ADA": return "ADAUSDT"
    if from_coin == "ADA" and to_coin == "BTC": return "ADABTC"
    if from_coin == "BTC" and to_coin == "ADA": return "ADABTC"
    if from_coin == "DOGE" and to_coin == "USDT": return "DOGEUSDT"
    if from_coin == "USDT" and to_coin == "DOGE": return "DOGEUSDT"
    if from_coin == "DOGE" and to_coin == "BTC": return "DOGEBTC"
    if from_coin == "BTC" and to_coin == "DOGE": return "DOGEBTC"
    return None

def _trade(book_data: dict, from_coin: str, to_coin: str, qty_in: float) -> tuple[float, str | None]:
    """Trade `qty_in` of from_coin into to_coin using book_data. Returns (qty_out, None) or (0, err)."""
    sym = _pair(from_coin, to_coin)
    if sym is None: return 0.0, "no pair"
    # If from_coin is the BASE of the pair (sym starts with from_coin), we SELL from_coin -> buy TO_COIN (quote)
    # If from_coin is the QUOTE (sym ends with from_coin), we BUY base with from_coin
    base, quote = sym[:-4], sym[-4:]
    if from_coin == base:
        # sell `qty_in` base -> receive quote
        out, err = _sell(book_data["bids"], qty_in)
        if err: return 0.0, err
        return out, None
    elif from_coin == quote:
        # spend `qty_in` quote -> buy base
        out, err = _consume(book_data["asks"], qty_in)
        if err: return 0.0, err
        return out, None
    return 0.0, "bad pair"

def scan(start_usdt: float = 1000.0, coins: list[str] = None, top_n: int = 25):
    """Find profitable triangular cycles starting/ending in USDT."""
    if coins is None:
        coins = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE"]
    # Build candidate cycles: USDT -> A -> B -> USDT for all ordered pairs A != B
    cycles = []
    for a, b in permutations(coins, 2):
        cycles.append(("USDT", a, b, "USDT"))

    # Pre-fetch all needed books
    needed_syms = set()
    for c in cycles:
        for i in range(len(c) - 1):
            s = _pair(c[i], c[i+1])
            if s: needed_syms.add(s)

    books = {}
    for s in needed_syms:
        try:
            books[s] = book(s)
        except Exception:
            continue

    results = []
    for c in cycles:
        # Check all legs have books
        legs = []
        ok = True
        for i in range(len(c) - 1):
            s = _pair(c[i], c[i+1])
            if not s or s not in books:
                ok = False
                break
            legs.append((c[i], c[i+1], books[s]))
        if not ok: continue

        # Walk the cycle
        qty = start_usdt
        trace = [f"start: {qty:.2f} USDT"]
        failed = False
        for from_coin, to_coin, bk in legs:
            out, err = _trade(bk, from_coin, to_coin, qty)
            if err:
                failed = True
                break
            qty = out
            trace.append(f"{from_coin}->{to_coin}: {qty:.6f}")

        if failed: continue

        gross_pct = (qty - start_usdt) / start_usdt * 100
        fees_pct = 3 * TAKER_FEE_PCT  # one taker fee per leg
        net_pct = gross_pct - fees_pct
        if net_pct <= 0: continue

        results.append({
            "cycle": " -> ".join(c),
            "start_usdt": start_usdt,
            "end_usdt": qty,
            "gross_pct": gross_pct,
            "fees_pct": fees_pct,
            "net_pct": net_pct,
            "trace": " | ".join(trace),
        })

    results.sort(key=lambda x: x["net_pct"], reverse=True)
    return results[:top_n]

def print_table(rows):
    if not rows:
        print("  No triangular arb cleared the bar (after 3-leg taker fees).")
        return
    print(f"{'Cycle':35s} {'Start$':>9s} {'End$':>10s} {'Gross%':>7s} {'Fees%':>6s} {'Net%':>7s}")
    for r in rows:
        print(f"{r['cycle']:35s} {r['start_usdt']:>9.0f} {r['end_usdt']:>10.4f} "
              f"{r['gross_pct']:>+7.3f} {r['fees_pct']:>6.3f} {r['net_pct']:>+7.3f}")
    print("\n  Note: triangular arb is highly competitive. Real edge requires")
    print("  execution within ~50ms and is dominated by HFT firms. Treat as")
    print("  a research signal, not a tradeable edge for manual execution.")

if __name__ == "__main__":
    rows = scan(start_usdt=10000)
    print(f"=== TRIANGULAR ARB {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
