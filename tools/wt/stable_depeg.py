"""Stablecoin depeg scanner.

When a stablecoin (USDC, USDT, DAI, FRAX, USDe, etc.) trades off $1.00,
there's an arbitrage opportunity:
  - If trading BELOW $1: buy stablecoin, redeem for $1 USDC (if redeemable)
  - If trading ABOVE $1: mint stablecoin with $1 USDC, sell at premium

This scanner watches all major stablecoins across Binance, Bybit, Gate, and
Curve (DEX) for depeg events > 10bps (0.10%).
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

STABLES = ["USDT", "USDC", "DAI", "TUSD", "FRAX", "USDe", "FDUSD", "PYUSD",
           "USDD", "GUSD", "LUSD", "SUSD", "USTC", "USDJ", "DOLA", "DEI",
           "MIM", "USD0", "USDM"]  # PAXG is gold but checks price

def binance_stables():
    """Get all stablecoin pairs vs USDT on Binance."""
    out = {}
    try:
        prices = {r["symbol"]: float(r["price"]) for r in _get("https://api.binance.com/api/v3/ticker/price")}
        vols = {r["symbol"]: float(r.get("quoteVolume", 0)) for r in _get("https://api.binance.com/api/v3/ticker/24hr")}
        for s in STABLES:
            pair = f"{s}USDT" if s != "USDT" else "USDCUSDT"  # for USDT use USDC pair
            if pair in prices:
                # Invert if needed (we want price of `s` in USDT)
                if s == "USDT":
                    out[s] = {"price": 1.0, "vol": vols.get(pair, 0), "venue": "binance"}
                else:
                    out[s] = {"price": prices[pair], "vol": vols.get(pair, 0), "venue": "binance"}
    except Exception as e:
        pass
    return out

def bybit_stables():
    out = {}
    try:
        d = _get("https://api.bybit.com/v5/market/tickers?category=spot")
        for t in d.get("result", {}).get("list", []):
            s = t.get("symbol", "")
            if s.endswith("USDT"):
                base = s[:-4]
                if base in STABLES and base != "USDT":
                    try:
                        p = float(t.get("lastPrice", 0))
                        v = float(t.get("turnover24h", 0))  # 24h quote volume
                        if p > 0:
                            out[base] = {"price": p, "vol": v, "venue": "bybit"}
                    except (TypeError, ValueError):
                        continue
    except Exception:
        pass
    return out

def gate_stables():
    out = {}
    try:
        g = _get("https://api.gateio.ws/api/v4/spot/tickers")
        for r in g:
            pair = r.get("currency_pair", "")
            if pair.endswith("_USDT"):
                base = pair.split("_")[0]
                if base in STABLES and base != "USDT":
                    try:
                        p = float(r.get("last", 0))
                        v = float(r.get("quote_volume", 0))
                        if p > 0:
                            out[base] = {"price": p, "vol": v, "venue": "gate"}
                    except (TypeError, ValueError):
                        continue
    except Exception:
        pass
    return out

def scan(min_depeg_bps: float = 10.0):
    """Find stablecoins trading >10bps off $1.00 across exchanges."""
    venues = {
        "binance": binance_stables(),
        "bybit": bybit_stables(),
        "gate": gate_stables(),
    }
    rows = []
    # Collect all stablecoins seen
    all_stables = set()
    for v in venues.values():
        all_stables.update(v.keys())
    for s in all_stables:
        prices = {vn: v[s]["price"] for vn, v in venues.items() if s in v}
        if not prices: continue
        # depeg = how far from $1.00 (avg across venues)
        avg_price = sum(prices.values()) / len(prices)
        depeg_bps = (avg_price - 1.0) * 10000
        if avg_price <= 0: continue  # skip zero prices (data error)
        if abs(depeg_bps) < min_depeg_bps: continue
        # also compute spread between exchanges
        if len(prices) >= 2:
            hi = max(prices.items(), key=lambda x: x[1])
            lo = min(prices.items(), key=lambda x: x[1])
            spread_bps = (hi[1] - lo[1]) * 10000
        else:
            hi = lo = (list(prices.items())[0] if prices else ("", 0))
            spread_bps = 0
        rows.append({
            "symbol": s,
            "avg_price": avg_price,
            "depeg_bps": depeg_bps,
            "hi_venue": hi[0], "hi_price": hi[1],
            "lo_venue": lo[0], "lo_price": lo[1],
            "spread_bps": spread_bps,
            "venues": list(prices.keys()),
        })
    rows.sort(key=lambda x: abs(x["depeg_bps"]), reverse=True)
    return rows

def print_table(rows):
    if not rows:
        print("  No stablecoin depeg > 10bps detected.")
        return
    print(f"{'Sym':8s} {'Avg$':>9s} {'DepegBps':>9s} {'HiVenue':10s} {'Hi$':>9s} {'LoVenue':10s} {'Lo$':>9s} {'SpreadBps':>10s}")
    for r in rows:
        print(f"{r['symbol']:8s} {r['avg_price']:>9.5f} {r['depeg_bps']:>+9.1f} "
              f"{r['hi_venue']:10s} {r['hi_price']:>9.5f} "
              f"{r['lo_venue']:10s} {r['lo_price']:>9.5f} {r['spread_bps']:>10.1f}")
    print("\n  Depeg > +30bps = stablecoin rich (mint + sell arb opportunity)")
    print("  Depeg < -30bps = stablecoin cheap (buy + redeem arb opportunity)")

if __name__ == "__main__":
    rows = scan()
    print(f"=== STABLECOIN DEPEG SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
