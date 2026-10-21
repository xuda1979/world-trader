"""Hyperliquid perp funding scanner.

Hyperliquid is a DEX with 1h funding intervals (vs Binance's 8h) and lists
many alts not on Binance. Funding arbs between Hyperliquid and Binance can
be substantial during volatility spikes.

Public API: https://api.hyperliquid.xyz/info (POST)
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8", "Content-Type": "application/json"}

def _post(url: str, body: dict, timeout: float = 15):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=UA, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def hl_meta():
    """Get all perps + funding info from Hyperliquid."""
    return _post("https://api.hyperliquid.xyz/info", {"type": "meta"})

def hl_asset_ctxs():
    """Get funding rates + open interest per asset."""
    return _post("https://api.hyperliquid.xyz/info", {"type": "metaAndAssetCtxs"})

def scan(min_funding_pct_1h: float = 0.01, top_n: int = 30):
    """Scan Hyperliquid perps for high funding rates (annualized)."""
    try:
        meta_and_ctxs = hl_asset_ctxs()
    except Exception as e:
        return [], f"hl error: {e}"
    if not isinstance(meta_and_ctxs, list) or len(meta_and_ctxs) < 2:
        return [], "hl unexpected response"
    meta = meta_and_ctxs[0]
    ctxs = meta_and_ctxs[1]
    universe = meta.get("universe", [])
    if len(universe) != len(ctxs):
        return [], "universe/ctxs length mismatch"

    rows = []
    for u, c in zip(universe, ctxs):
        name = u.get("name", "")
        if not name: continue
        try:
            fr = float(c.get("funding", 0)) * 100  # already a fraction; *100 = % per 1h
        except (TypeError, ValueError):
            continue
        if abs(fr) < min_funding_pct_1h: continue
        try:
            oi = float(c.get("openInterest", 0))
            mark_px = float(c.get("markPx", 0))
            oi_usd = oi * mark_px
        except (TypeError, ValueError):
            oi_usd = 0
        apr = fr * 24 * 365  # 1h intervals -> 24/day -> *365
        rows.append({
            "symbol": name,
            "fr_pct_1h": fr,
            "apr_pct": apr,
            "oi_usd": oi_usd,
            "mark": mark_px,
        })
    rows.sort(key=lambda x: abs(x["apr_pct"]), reverse=True)
    return rows[:top_n], None

def print_table(rows):
    if not rows:
        print("  No Hyperliquid funding candidates.")
        return
    print(f"{'Sym':16s} {'FR%/1h':>8s} {'APR%':>10s} {'OI$M':>9s} {'Mark':>12s}")
    for r in rows:
        print(f"{r['symbol']:16s} {r['fr_pct_1h']:>+8.4f} {r['apr_pct']:>+10.1f} "
              f"{r['oi_usd']/1e6:>9.1f} {r['mark']:>12.4f}")

if __name__ == "__main__":
    rows, err = scan()
    print(f"=== HYPERLIQUID FUNDING {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    if err: print(err)
    else: print_table(rows)
