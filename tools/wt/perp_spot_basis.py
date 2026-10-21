"""Perp vs spot basis arbitrage on the same exchange (Binance).

When a perp trades at a sustained premium to spot:
  - LONG spot + SHORT perp
  - If perp stays above spot at funding time, you collect funding
  - If perp converges to spot, you also capture the basis

This is simpler than cross-exchange arb (no transfer risk, single venue)
but usually has smaller edge.

Edge = funding_per_event * projected_events + basis_convergence - fees.
"""
from __future__ import annotations
import urllib.request, json, time

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def scan(min_volume_m: float = 20.0, min_basis_pct: float = 0.05,
         projected_events: int = 3, top_n: int = 25):
    """Single-exchange perp vs spot basis + funding combined edge."""
    perps = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    spot_24h = {r["symbol"]: float(r.get("quoteVolume", 0))
                for r in _get("https://api.binance.com/api/v3/ticker/24hr")}
    spot_prices = {r["symbol"]: float(r["price"]) for r in _get("https://api.binance.com/api/v3/ticker/price")}

    cands = []
    for p in perps:
        sym = p.get("symbol", "")
        if not sym.endswith("USDT"): continue
        if sym not in spot_prices: continue  # need spot listing
        sv = spot_24h.get(sym, 0)
        if sv < min_volume_m * 1e6: continue
        try:
            mark = float(p.get("markPrice", 0))
            fr = float(p.get("lastFundingRate", 0)) * 100  # % per 8h
        except (TypeError, ValueError):
            continue
        spot = spot_prices[sym]
        if mark <= 0 or spot <= 0: continue
        basis_pct = (mark - spot) / spot * 100
        if abs(basis_pct) < min_basis_pct: continue

        # If perp at PREMIUM (basis > 0): LONG spot + SHORT perp
        #   Capture: basis converges to 0 + collect funding (because positive funding
        #   means longs pay shorts, and we're short the perp)
        # If perp at DISCOUNT (basis < 0): SHORT spot (margin) + LONG perp
        #   Capture: basis converges to 0 + pay funding (negative funding means
        #   shorts pay longs, so we collect if fr < 0)
        if basis_pct > 0:
            funding_capture = max(fr, 0) * projected_events  # we're short, collect positive funding
            direction = "long_spot_short_perp"
        else:
            funding_capture = max(-fr, 0) * projected_events  # we're long, collect negative funding
            direction = "short_spot_long_perp"

        # Fees: entry+exit, both legs, maker
        fees = 2 * (0.02 + 0.075)
        gross = abs(basis_pct) + funding_capture
        net = gross - fees
        if net <= 0: continue
        cands.append({
            "symbol": sym, "spot": spot, "mark": mark,
            "basis_pct": basis_pct, "fr_pct_8h": fr,
            "funding_capture_pct": funding_capture,
            "fees_pct": fees, "net_pct_24h": net,
            "apr_pct": net / projected_events * 365,
            "spot_vol_m": sv / 1e6,
            "direction": direction,
        })

    cands.sort(key=lambda x: x["net_pct_24h"], reverse=True)
    return cands[:top_n]

def print_table(rows):
    if not rows:
        print("  No perp-spot basis candidates cleared the bar.")
        return
    print(f"{'Sym':12s} {'Basis%':>7s} {'FR%/8h':>7s} {'FundCap%':>8s} {'Fees%':>6s} {'Net%/24h':>9s} {'APR%':>7s} {'Vol$M':>7s} {'Direction':22s}")
    for r in rows:
        print(f"{r['symbol']:12s} {r['basis_pct']:>+7.3f} {r['fr_pct_8h']:>+7.4f} "
              f"{r['funding_capture_pct']:>8.3f} {r['fees_pct']:>6.3f} "
              f"{r['net_pct_24h']:>+9.3f} {r['apr_pct']:>+7.1f} {r['spot_vol_m']:>7.0f} {r['direction']:22s}")

if __name__ == "__main__":
    rows = scan()
    print(f"=== PERP-SPOT BASIS ARB {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
