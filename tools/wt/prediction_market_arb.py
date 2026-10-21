"""Prediction market arbitrage: Polymarket.

For binary markets (Yes/No), if YES price + NO price != $1.00, there's an
arb: buy the cheaper side, hold to resolution. Guaranteed payout of $1.

Edge = $1.00 - (yes_price + no_price) - fees.
Polymarket fees: ~0% on trades, 2% on winnings.

Public API: https://gamma-api.polymarket.com/markets
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "Mozilla/5.0 (compatible; arb-scanner/1.0)"}

def _get(url: str, timeout: float = 15):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def fetch_markets(limit: int = 200, active_only: bool = True):
    """Fetch active binary markets from Polymarket."""
    url = f"https://gamma-api.polymarket.com/markets?limit={limit}&active=true&closed=false&order=volume24hr&ascending=false"
    return _get(url, timeout=20)

def scan(min_edge_pct: float = 2.0, min_volume: float = 5000.0):
    """Find markets where YES + NO < $0.98 (after 2% fee on winnings)."""
    rows = []
    try:
        markets = fetch_markets(limit=300)
    except Exception as e:
        return [], f"fetch error: {e}"

    for m in markets:
        # Polymarket markets can be single-markets or have outcomes array
        outcomes = m.get("outcomes", [])
        outcome_prices = m.get("outcomePrices", "")
        if not outcomes or not outcome_prices:
            continue
        try:
            # outcomePrices may be a JSON string
            if isinstance(outcome_prices, str):
                prices = json.loads(outcome_prices)
            else:
                prices = outcome_prices
            prices = [float(p) for p in prices]
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if len(prices) != 2: continue  # only binary markets
        yes, no = prices[0], prices[1]
        total = yes + no
        # We want to BUY both sides for less than $1
        # Cost = yes + no, payout = $1 (one side wins)
        # Edge = 1 - total - 0.02 (fee on $1 winnings = $0.02)
        edge_pct = (1.0 - total - 0.02) * 100
        if edge_pct < min_edge_pct: continue
        try:
            vol = float(m.get("volume24hr", 0) or 0)
        except (TypeError, ValueError):
            vol = 0
        if vol < min_volume: continue
        rows.append({
            "question": m.get("question", "")[:80],
            "yes_price": yes,
            "no_price": no,
            "total": total,
            "edge_pct": edge_pct,
            "volume_24h": vol,
            "end_date": (m.get("endDate") or "")[:10],
            "url": m.get("slug", ""),
        })
    rows.sort(key=lambda x: x["edge_pct"], reverse=True)
    return rows, None

def print_table(rows, err):
    if err:
        print(f"  Error: {err}")
        return
    if not rows:
        print("  No prediction market arb > 2% detected.")
        return
    print(f"{'Market':60s} {'YES':>6s} {'NO':>6s} {'Total':>6s} {'Edge%':>6s} {'Vol24h':>10s} {'End':10s}")
    for r in rows[:15]:
        print(f"{r['question'][:60]:60s} {r['yes_price']:>6.3f} {r['no_price']:>6.3f} "
              f"{r['total']:>6.3f} {r['edge_pct']:>+6.2f} ${r['volume_24h']:>9.0f} {r['end_date']:10s}")
    print("\n  Edge > 2% = guaranteed profit if held to resolution (buy YES + NO for < $0.98)")
    print("  Risk: market resolution delay, dispute risk, smart contract risk")

if __name__ == "__main__":
    rows, err = scan()
    print(f"=== PREDICTION MARKET ARB (Polymarket) {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows, err)
