"""Crypto calendar spread arbitrage (Binance quarterlies).

When two quarterlies for the same underlying trade at inconsistent basis:
  - e.g., BTC Sept 2026 mark = +0.76% over spot
  -       BTC Dec 2026 mark = +1.67% over spot
  - Spread = 0.91% between quarterlies

If we believe the term structure should be smoother, we can:
  - SHORT Dec quarterly (richer basis) + LONG Sept quarterly (cheaper basis)
  - Net delta = 0, capture the spread convergence

The trade PAYS OFF if the basis spread narrows. Risk: spread widens.

This scanner detects large calendar spreads and reports them.
"""
from __future__ import annotations
import urllib.request, json, time
from datetime import datetime

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def scan(min_spread_bps: float = 30.0):
    """Find calendar spreads between Binance quarterlies."""
    pi = _get("https://fapi.binance.com/fapi/v1/premiumIndex")
    spot_prices = {r["symbol"]: float(r["price"]) for r in _get("https://api.binance.com/api/v3/ticker/price")}

    # Group quarterlies by base
    by_base = {}
    for r in pi:
        s = r.get("symbol", "")
        if "_" not in s: continue
        base, suffix = s.split("_", 1)
        if not base.endswith("USDT"): continue
        try:
            mark = float(r.get("markPrice", 0))
        except (TypeError, ValueError):
            continue
        if mark <= 0: continue
        spot = spot_prices.get(base)
        if not spot: continue
        basis_pct = (mark - spot) / spot * 100
        try:
            exp_date = datetime.strptime("20" + suffix, "%Y%m%d")
            days = (exp_date - datetime.now()).days
        except Exception:
            continue
        if days <= 0: continue
        by_base.setdefault(base, []).append({
            "symbol": s, "mark": mark, "spot": spot, "basis_pct": basis_pct,
            "days": days, "apr_pct": basis_pct / days * 365,
        })

    # Find calendar spreads within each base
    rows = []
    for base, contracts in by_base.items():
        if len(contracts) < 2: continue
        # sort by days
        contracts.sort(key=lambda x: x["days"])
        for i in range(len(contracts) - 1):
            for j in range(i + 1, len(contracts)):
                near = contracts[i]
                far = contracts[j]
                spread_bps = (far["basis_pct"] - near["basis_pct"]) * 100  # in bps
                if abs(spread_bps) < min_spread_bps: continue
                # APR of the spread (over the near contract's days)
                spread_apr = (far["basis_pct"] - near["basis_pct"]) / near["days"] * 365
                rows.append({
                    "base": base,
                    "near_sym": near["symbol"],
                    "far_sym": far["symbol"],
                    "near_basis_pct": near["basis_pct"],
                    "far_basis_pct": far["basis_pct"],
                    "spread_bps": spread_bps,
                    "spread_apr_pct": spread_apr,
                    "near_days": near["days"],
                    "far_days": far["days"],
                    "trade": "short_far_long_near" if spread_bps > 0 else "long_far_short_near",
                })
    rows.sort(key=lambda x: abs(x["spread_bps"]), reverse=True)
    return rows

def print_table(rows):
    if not rows:
        print("  No calendar spread > 30bps detected.")
        return
    print(f"{'Base':10s} {'Near':22s} {'Far':22s} {'NearB%':>7s} {'FarB%':>7s} {'SpreadBps':>10s} {'SpreadAPR%':>10s} {'Trade':22s}")
    for r in rows[:10]:
        print(f"{r['base']:10s} {r['near_sym']:22s} {r['far_sym']:22s} "
              f"{r['near_basis_pct']:>+7.3f} {r['far_basis_pct']:>+7.3f} "
              f"{r['spread_bps']:>+10.1f} {r['spread_apr_pct']:>+10.2f} {r['trade']:22s}")
    print("\n  Spread > +30bps = far quarter is rich vs near; SHORT far + LONG near (delta-neutral)")
    print("  Risk: spread can widen before converging. Defined risk via position sizing.")

if __name__ == "__main__":
    rows = scan()
    print(f"=== CALENDAR SPREAD ARB {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)
