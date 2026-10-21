"""Curve pool depeg arbitrage.

Curve pools (e.g., 3pool = USDC/USDT/DAI, stETH-ETH pool) trade assets that
should be $1.00 (or 1:1 for stETH/ETH). When pool balances shift, you can
arb by depositing the underweight asset and withdrawing the overweight one.

Public API: https://api.curve.fi/v1/getPools/all
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 15):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def fetch_curve_pools():
    """Fetch all Curve pools with current virtual prices and balances."""
    url = "https://api.curve.fi/api/getPools/all"
    try:
        return _get(url, timeout=20)
    except Exception:
        # Fallback to v1
        try:
            return _get("https://api.curve.fi/v1/getPools/all", timeout=20)
        except Exception as e:
            return None

def scan(min_depeg_bps: float = 5.0):
    """Find Curve pools where assets trade off-peg."""
    rows = []
    data = fetch_curve_pools()
    if not data:
        return [], "curve API unavailable"
    pools = data.get("data", {}).get("poolData", []) if isinstance(data, dict) else []
    if not pools:
        # Try alternate structure
        pools = data.get("poolData", []) if isinstance(data, dict) else []
    for p in pools:
        name = p.get("name", "")
        pool_type = p.get("poolType", "")
        # Get coin addresses and prices
        coins = p.get("coins", [])
        if not coins: continue
        # Get underlying coin prices from pool
        # Curve's 'underlyingCoins' usually have prices
        usd_prices = []
        for c in coins:
            try:
                usd_price = float(c.get("usdPrice", 0) or 0)
                if usd_price > 0:
                    usd_prices.append((c.get("symbol", ""), usd_price))
            except (TypeError, ValueError):
                continue
        if len(usd_prices) < 2: continue
        # For stablecoin pools, all should be ~$1
        # For stETH/ETH pool, both should be ~same price
        is_stable_pool = all(0.9 < p < 1.1 for _, p in usd_prices)
        if not is_stable_pool: continue
        # Compute max depeg among coins
        prices = [p for _, p in usd_prices]
        if not prices: continue
        avg = sum(prices) / len(prices)
        for sym, px in usd_prices:
            depeg_bps = (px - avg) / avg * 10000 if avg > 0 else 0
            if abs(depeg_bps) >= min_depeg_bps:
                rows.append({
                    "pool": name,
                    "pool_type": pool_type,
                    "coin": sym,
                    "price": px,
                    "avg_pool_price": avg,
                    "depeg_bps": depeg_bps,
                })
    rows.sort(key=lambda x: abs(x["depeg_bps"]), reverse=True)
    return rows, None

def print_table(rows, err):
    if err:
        print(f"  Error: {err}")
        return
    if not rows:
        print("  No Curve pool depeg > 5bps detected.")
        return
    print(f"{'Pool':30s} {'Type':12s} {'Coin':10s} {'Price':>9s} {'AvgPool$':>9s} {'DepegBps':>9s}")
    for r in rows[:15]:
        print(f"{r['pool'][:30]:30s} {r['pool_type'][:12]:12s} {r['coin']:10s} "
              f"{r['price']:>9.5f} {r['avg_pool_price']:>9.5f} {r['depeg_bps']:>+9.1f}")
    print("\n  Depeg > +10bps = coin rich in pool, deposit other coin + withdraw this one")
    print("  Execution: needs Ethereum gas, ~$10-30 per trade")

if __name__ == "__main__":
    rows, err = scan()
    print(f"=== CURVE POOL DEPEG {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows, err)
