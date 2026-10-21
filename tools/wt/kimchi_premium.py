"""Kimchi premium scanner: Korean BTC price vs US price.

Korean exchanges (Upbit, Bithumb, Korbit) often trade BTC at a premium or
discount to US exchanges due to capital controls. During volatility, the
"kimchi premium" can hit 5-10%.

Real arbitrage requires Korean bank account + KYC, so this is research only
for most users. But the SIGNAL tells you when Korean retail is panicking
or euphoric — useful directional signal for global crypto.

Public APIs (no key):
  Upbit:  https://api.upbit.com/v1/ticker?markets=USDT-BTC,KRW-BTC
  Bithumb: https://api.bithumb.com/public/ticker/BTC_KRW
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

# Approximate USD/KRW rate (could use FRED or exchangerate-api)
def usd_krw_rate() -> float:
    """Get USD/KRW rate from exchangerate-api (free, no key)."""
    try:
        d = _get("https://open.er-api.com/v6/latest/USD")
        return float(d.get("rates", {}).get("KRW", 1380))
    except Exception:
        return 1380.0  # fallback

def upbit_krw_btc() -> tuple[float, float] | None:
    """Upbit KRW-BTC price + 24h volume in KRW."""
    try:
        d = _get("https://api.upbit.com/v1/ticker?markets=KRW-BTC")
        if d and len(d) > 0:
            return float(d[0].get("trade_price", 0)), float(d[0].get("acc_trade_price_24h", 0))
    except Exception:
        pass
    return None

def upbit_usdt_btc() -> float | None:
    """Upbit USDT-BTC (the global market on Upbit)."""
    try:
        d = _get("https://api.upbit.com/v1/ticker?markets=USDT-BTC")
        if d and len(d) > 0:
            return float(d[0].get("trade_price", 0))
    except Exception:
        pass
    return None

def bithumb_krw_btc() -> tuple[float, float] | None:
    try:
        d = _get("https://api.bithumb.com/public/ticker/BTC_KRW")
        data = d.get("data", {})
        return float(data.get("closing_price", 0)), float(data.get("acc_trade_value_24h", 0))
    except Exception:
        pass
    return None

def binance_btc_usd() -> tuple[float, float] | None:
    """Binance BTCUSDT price + 24h quote volume."""
    try:
        p = float(_get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")["price"])
        v = float(_get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT").get("quoteVolume", 0))
        return p, v
    except Exception:
        return None

def scan(min_premium_bps: float = 30.0):
    """Compute kimchi premium vs Binance USDT."""
    rows = []
    fx = usd_krw_rate()
    bn = binance_btc_usd()
    if not bn: return rows, "binance unavailable"
    bn_usd, bn_vol = bn
    bn_krw_equiv = bn_usd * fx

    venues = {
        "upbit_krw": upbit_krw_btc(),
        "bithumb_krw": bithumb_krw_btc(),
    }
    upbit_usdt = upbit_usdt_btc()
    if upbit_usdt:
        # Upbit USDT market in USD equivalent
        venues["upbit_usdt"] = (upbit_usdt, 0)

    for name, val in venues.items():
        if not val or val[0] <= 0: continue
        krw_price = val[0]
        vol_krw = val[1] if len(val) > 1 else 0
        # convert to USD equivalent for comparison
        usd_equiv = krw_price / fx if "krw" in name else krw_price
        premium_bps = (usd_equiv - bn_usd) / bn_usd * 10000
        if abs(premium_bps) < min_premium_bps: continue
        rows.append({
            "venue": name,
            "local_price": krw_price,
            "usd_equiv": usd_equiv,
            "binance_usd": bn_usd,
            "fx_usd_krw": fx,
            "premium_bps": premium_bps,
            "premium_pct": premium_bps / 100,
            "vol_krw_m": vol_krw / 1e6,
        })
    rows.sort(key=lambda x: abs(x["premium_bps"]), reverse=True)
    return rows, None

def print_table(rows, err):
    if err:
        print(f"  Error: {err}")
        return
    if not rows:
        print("  No kimchi premium > 30bps detected.")
        return
    print(f"{'Venue':14s} {'Local':>12s} {'USDEquiv':>10s} {'Binance$':>10s} {'FX':>7s} {'PremBps':>8s} {'Prem%':>7s} {'Vol$M':>8s}")
    for r in rows:
        vol_usd_m = r["vol_krw_m"] / r["fx_usd_krw"] if r["fx_usd_krw"] > 0 else 0
        print(f"{r['venue']:14s} {r['local_price']:>12.0f} {r['usd_equiv']:>10.2f} "
              f"{r['binance_usd']:>10.2f} {r['fx_usd_krw']:>7.0f} "
              f"{r['premium_bps']:>+8.1f} {r['premium_pct']:>+7.3f} {vol_usd_m:>8.1f}")
    print("\n  Premium > +50bps = Korean retail FOMO (signal: global crypto may follow)")
    print("  Premium < -50bps = Korean retail panic (signal: local selling pressure)")

if __name__ == "__main__":
    rows, err = scan()
    print(f"=== KIMCHI PREMIUM {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows, err)
