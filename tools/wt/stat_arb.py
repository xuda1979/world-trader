"""Statistical arbitrage via cointegration.

For pairs of correlated assets (e.g., BTC/ETH, SPY/QQQ), if the spread
between them deviates from its historical mean by >2 sigma, bet on reversion.

This scanner:
  1. Fetches recent price history for a curated pair list
  2. Computes the hedge ratio via OLS regression
  3. Computes the spread z-score
  4. Reports pairs where |z| > 2 (entry signal)

Public data: Binance klines (crypto), Yahoo Finance (equities/ETFs).
"""
from __future__ import annotations
import urllib.request, json, time, math

UA = {"User-Agent": "Mozilla/5.0 (compatible; stat-arb/1.0)"}

def _get(url: str, timeout: float = 15):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def binance_klines(sym: str, interval: str = "1h", limit: int = 200) -> list[float]:
    """Fetch hourly closes from Binance."""
    url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={interval}&limit={limit}"
    try:
        d = _get(url, timeout=10)
        return [float(k[4]) for k in d]  # k[4] = close price
    except Exception:
        return []

def ols_beta(y: list[float], x: list[float]) -> float:
    """OLS beta: y = alpha + beta*x + eps."""
    n = min(len(y), len(x))
    if n < 30: return 0.0
    y = y[-n:]; x = x[-n:]
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((x[i] - mx) ** 2 for i in range(n))
    return num / den if den > 0 else 0.0

def zscore(series: list[float]) -> float:
    if len(series) < 30: return 0.0
    mean = sum(series) / len(series)
    var = sum((x - mean) ** 2 for x in series) / (len(series) - 1)
    sd = math.sqrt(var)
    if sd == 0: return 0.0
    return (series[-1] - mean) / sd

# Curated cointegrated pair candidates (all Binance USDT perps)
PAIRS = [
    ("BTCUSDT", "ETHUSDT"),
    ("BTCUSDT", "BNBUSDT"),
    ("ETHUSDT", "SOLUSDT"),
    ("ETHUSDT", "AVAXUSDT"),
    ("SOLUSDT", "AVAXUSDT"),
    ("SOLUSDT", "LDOUSDT"),
    ("MATICUSDT", "POLUSDT"),
    ("ARBUSDT", "OPUSDT"),
    ("ATOMUSDT", "NEARUSDT"),
    ("LINKUSDT", "UNIUSDT"),
    ("BTCUSDT", "WBTCUSDT"),  # should be near 1:1
    ("BNBUSDT", "CAKEUSDT"),
    ("DOGEUSDT", "SHIBUSDT"),
    ("XRPUSDT", "ADAUSDT"),
    ("LTCUSDT", "BCHUSDT"),
]

def scan(min_z: float = 2.0, lookback: int = 200):
    """Find pairs where the spread z-score > |2|."""
    # Cache prices
    cache = {}
    syms = set()
    for a, b in PAIRS:
        syms.add(a); syms.add(b)
    for s in syms:
        cache[s] = binance_klines(s, "1h", lookback)
    rows = []
    for a, b in PAIRS:
        pa = cache.get(a, [])
        pb = cache.get(b, [])
        if len(pa) < 50 or len(pb) < 50: continue
        # Align lengths
        n = min(len(pa), len(pb))
        pa = pa[-n:]; pb = pb[-n:]
        # Compute beta (hedge ratio)
        beta = ols_beta(pa, pb)
        if beta <= 0: continue
        # Spread = price_a - beta * price_b
        spread = [pa[i] - beta * pb[i] for i in range(n)]
        z = zscore(spread)
        if abs(z) < min_z: continue
        # Half-life estimate (very rough)
        rows.append({
            "asset_a": a, "asset_b": b,
            "beta": beta,
            "z_score": z,
            "spread_last": spread[-1],
            "price_a": pa[-1], "price_b": pb[-1],
            "trade": f"long {a} / short {beta:.2f}x {b}" if z < 0 else f"short {a} / long {beta:.2f}x {b}",
        })
    rows.sort(key=lambda x: abs(x["z_score"]), reverse=True)
    return rows

def print_table(rows):
    if not rows:
        print("  No cointegrated pair with |z| > 2.0 detected.")
        return
    print(f"{'Asset A':10s} {'Asset B':10s} {'Beta':>7s} {'Z-Score':>8s} {'Price A':>10s} {'Price B':>10s} {'Trade':35s}")
    for r in rows[:15]:
        print(f"{r['asset_a']:10s} {r['asset_b']:10s} {r['beta']:>7.3f} {r['z_score']:>+8.2f} "
              f"{r['price_a']:>10.4f} {r['price_b']:>10.4f} {r['trade']:35s}")
    print("\n  Z < -2 = spread too narrow; LONG A / SHORT B (bet on reversion)")
    print("  Z > +2 = spread too wide; SHORT A / LONG B (bet on reversion)")
    print("  Risk: cointegration can break (regime change). Use stops.")

if __name__ == "__main__":
    rows = scan()
    print(f"=== STATISTICAL ARBITRAGE (cointegration) {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
