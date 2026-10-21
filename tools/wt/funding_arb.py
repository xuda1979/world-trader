"""Funding-rate arbitrage scanner (Binance USDT-M perps vs spot).

Strategy:
  When a perp's funding rate is high AND positive, longs pay shorts.
  We capture it delta-neutral: LONG spot + SHORT perp. Net delta ~0,
  we collect funding every 8h. Conversely for negative funding.

  Edge = (funding_per_8h * projected_events) - round_trip_fees - basis_convergence_cost.

This is research only, not financial advice. Live trading requires
your own verification of fees, funding timestamps, and exchange rules.
"""
from __future__ import annotations
import urllib.request, json, time
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "curl/8"}

def _get(url: str, timeout: float = 10):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=timeout))

# ---------- Binance public endpoints ----------
def all_perp_funding():
    """All USDT-M perp funding rates + mark prices."""
    return _get("https://fapi.binance.com/fapi/v1/premiumIndex")

def all_perp_volume():
    """24h quote volume for every perp."""
    rows = _get("https://fapi.binance.com/fapi/v1/ticker/24hr")
    return {r["symbol"]: float(r.get("quoteVolume", 0)) for r in rows}

def spot_price(sym: str):
    return float(_get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT")["price"])

def spot_prices(symbols: list[str]):
    """Batch spot prices via /api/v3/ticker/price without symbol -> all prices."""
    out = {}
    try:
        allp = _get("https://api.binance.com/api/v3/ticker/price")
        smap = {r["symbol"]: float(r["price"]) for r in allp}
        for s in symbols:
            if f"{s}USDT" in smap:
                out[s] = smap[f"{s}USDT"]
    except Exception:
        for s in symbols:
            try: out[s] = spot_price(s)
            except Exception: pass
    return out

# ---------- Scanner ----------
def scan(
    min_quote_volume_m: float = 20.0,        # $20M 24h volume (perp)
    min_spot_volume_m: float = 5.0,          # $5M 24h spot volume (liquidity to enter/exit)
    min_funding_pct_8h: float = 0.02,        # 0.02% per 8h = ~22% APR gross
    max_basis_pct: float = 0.30,             # don't trade if perp basis > 0.30% (costs eat edge)
    maker_fee_pct: float = 0.02,             # Binance perp maker (0.02%, VIP0 + BNB)
    spot_maker_pct: float = 0.075,           # Binance spot maker (0.075% with BNB)
    projected_events: int = 3,               # hold through 3 funding events (24h)
    top_n: int = 25,
    require_spot: bool = True,               # only return symbols with Binance spot listing
):
    """Return ranked list of funding-arb candidates.

    For each candidate:
      - If funding > 0: LONG spot + SHORT perp (collect funding from longs).
      - If funding < 0: SHORT spot (margin) + LONG perp (collect funding from shorts).
        For simplicity here we focus on the long-spot/short-perp variant since
        shorting spot on Binance is harder (margin) and rates differ.

    Edge per 8h = funding% - (basis_cost / events_held) - fees_amortized.
    """
    funding_rows = all_perp_funding()
    vol = all_perp_volume()

    # spot volume + spot price lookup
    try:
        spot_24h = _get("https://api.binance.com/api/v3/ticker/24hr")
        spot_vol = {r["symbol"]: float(r.get("quoteVolume", 0)) for r in spot_24h}
    except Exception:
        spot_vol = {}
    try:
        spot_all_prices = {r["symbol"]: float(r["price"]) for r in _get("https://api.binance.com/api/v3/ticker/price")}
    except Exception:
        spot_all_prices = {}

    # filter to USDT perps with sufficient volume AND a spot listing
    cands = []
    for r in funding_rows:
        sym = r.get("symbol", "")
        if not sym.endswith("USDT"): continue
        qv = vol.get(sym, 0.0)
        if qv < min_quote_volume_m * 1e6: continue
        if require_spot and sym not in spot_all_prices:
            continue
        sv = spot_vol.get(sym, 0.0)
        if require_spot and sv < min_spot_volume_m * 1e6:
            continue
        try:
            fr = float(r.get("lastFundingRate", 0)) * 100  # % per 8h
        except (TypeError, ValueError):
            continue
        if abs(fr) < min_funding_pct_8h: continue
        cands.append({"symbol": sym, "fr_pct": fr, "quote_vol": qv,
                      "spot_vol": sv, "mark": float(r.get("markPrice", 0))})

    # batch spot prices
    base_syms = [c["symbol"].replace("USDT", "") for c in cands]
    sps = spot_prices(base_syms)
    for c in cands:
        b = c["symbol"].replace("USDT", "")
        c["spot"] = sps.get(b)
        if c["spot"]:
            c["basis_pct"] = (c["mark"] - c["spot"]) / c["spot"] * 100
        else:
            c["basis_pct"] = None

    # filter by basis
    cands = [c for c in cands if c["basis_pct"] is not None and abs(c["basis_pct"]) <= max_basis_pct]

    # economics — maker fees on both legs, entry + exit
    # entry: 1 perp fill + 1 spot fill; exit: 1 perp fill + 1 spot fill
    rt_fees_pct = 2 * (maker_fee_pct + spot_maker_pct)
    # if funding > 0: short perp + long spot. PnL = funding - |basis| (perp converges to spot) - fees
    # if funding < 0: long perp + short spot. PnL = |funding| - |basis| - fees (short spot costs not counted)
    for c in cands:
        gross_funding_pct = abs(c["fr_pct"]) * projected_events
        basis_cost = abs(c["basis_pct"])
        fee_cost = rt_fees_pct
        net_pct = gross_funding_pct - basis_cost - fee_cost
        c["gross_funding_pct"] = gross_funding_pct
        c["basis_cost_pct"] = basis_cost
        c["fee_cost_pct"] = fee_cost
        c["net_pct_24h"] = net_pct
        c["apr_pct"] = net_pct / projected_events * 365
        c["direction"] = "short_perp_long_spot" if c["fr_pct"] > 0 else "long_perp_short_spot"

    # drop negative-edge rows from final list (keep zero/+ only)
    cands = [c for c in cands if c["net_pct_24h"] > 0]
    cands.sort(key=lambda x: x["net_pct_24h"], reverse=True)
    return cands[:top_n]

def print_table(rows):
    if not rows:
        print("  no funding-arb candidates cleared the bar.")
        return
    hdr = ["Sym", "FR%/8h", "Vol$M", "Basis%", "Gross%", "BasisCost%", "Fees%", "Net%/24h", "APR%", "Direction"]
    al = [">", ">", ">", ">", ">", ">", ">", ">", ">", "<"]
    body = []
    for r in rows:
        body.append([
            r["symbol"],
            f"{r['fr_pct']:+.4f}",
            f"{r['quote_vol']/1e6:.0f}",
            f"{r['basis_pct']:+.3f}",
            f"{r['gross_funding_pct']:.3f}",
            f"{r['basis_cost_pct']:.3f}",
            f"{r['fee_cost_pct']:.3f}",
            f"{r['net_pct_24h']:+.3f}",
            f"{r['apr_pct']:+.1f}",
            r["direction"],
        ])
    # simple table printer (no external dep)
    widths = [max(len(str(h)), max((len(b[i]) for b in body), default=0)) for i, h in enumerate(hdr)]
    sep = "  "
    def fmt_row(vals): return sep.join(str(v).rjust(widths[i]) for i, v in enumerate(vals))
    print("  " + fmt_row(hdr))
    print("  " + sep.join("-" * w for w in widths))
    for b in body:
        print("  " + fmt_row(b))
    print("\n  Edge% is gross funding over 24h (3 events) minus basis convergence and fees.")
    print("  Negative basis is BONUS (perp below spot means short-perp captures basis as convergence gain).")

if __name__ == "__main__":
    rows = scan()
    print(f"=== FUNDING ARB SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")
    print_table(rows)


# ---------- Quarterly futures basis (cash and carry) ----------
def quarterly_basis_scan():
    """Binance quarterly BTC/ETH futures vs spot — annualized basis.

    Cash-and-carry: long spot + short quarterly = collect basis as it
    converges to zero at expiry. Delta-neutral, defined risk.

    Edge = basis% (converges to 0 at expiry) - round_trip_fees.
    """
    from datetime import datetime
    try:
        pi = all_perp_funding()  # premiumIndex includes quarterly marks
    except Exception:
        pi = []
    try:
        all_p = _get("https://api.binance.com/api/v3/ticker/price")
        spmap = {r["symbol"]: float(r["price"]) for r in all_p}
    except Exception:
        spmap = {}

    pmap = {r.get("symbol", ""): r for r in pi}
    results = []
    for sym, r in pmap.items():
        # quarterlies look like BTCUSDT_261225 (base+USDT_YYMMDD)
        if "_" not in sym: continue
        base, suffix = sym.split("_", 1)
        if not base.endswith("USDT"): continue
        try:
            mark = float(r.get("markPrice", 0))
        except (TypeError, ValueError):
            continue
        if mark <= 0: continue
        base = sym.split("_")[0]
        spot = spmap.get(base)
        if not spot: continue
        basis_pct = (mark - spot) / spot * 100
        # parse expiry
        try:
            exp = sym.split("_")[1]
            exp_date = datetime.strptime("20" + exp, "%Y%m%d")
            days = (exp_date - datetime.now()).days
        except Exception:
            continue
        if days <= 0: continue
        apr = basis_pct / days * 365
        # fees: 2 entries + 2 exits (spot + futures) at maker
        # convergence guaranteed at expiry so we ignore basis risk
        fees = 2 * (0.02 + 0.075)  # perp maker + spot maker, both sides
        net_pct = basis_pct - fees
        net_apr = net_pct / days * 365
        results.append({
            "symbol": sym, "base": base, "mark": mark, "spot": spot,
            "basis_pct": basis_pct, "days": days, "apr_pct": apr,
            "fees_pct": fees, "net_pct": net_pct, "net_apr_pct": net_apr,
            "direction": "long_spot_short_quarterly" if basis_pct > 0 else "short_spot_long_quarterly",
        })
    results.sort(key=lambda x: x["net_apr_pct"], reverse=True)
    return results

def print_quarterly(rows):
    if not rows:
        print("  No quarterly-futures basis candidates.")
        return
    print(f"{'Sym':22s} {'Base':8s} {'Mark':>12s} {'Spot':>12s} {'Basis%':>7s} {'Days':>5s} {'APR%':>7s} {'NetAPR%':>8s}")
    for r in rows:
        print(f"{r['symbol']:22s} {r['base']:8s} {r['mark']:>12.2f} {r['spot']:>12.2f} "
              f"{r['basis_pct']:>+7.3f} {r['days']:>5d} {r['apr_pct']:>+7.2f} {r['net_apr_pct']:>+8.2f}")
