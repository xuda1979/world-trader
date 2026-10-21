#!/usr/bin/env python3
"""30-minute loop scan: 6 arbitrage scanners.

  1) Single-exchange funding arb (Binance spot vs perp)
  2) Cross-exchange funding spread (Binance/Bybit/OKX/Gate/Bitget)
  3) Order-book-verified cross-exchange spot arb
  4) Quarterly futures basis (cash and carry)
  5) Triangular arbitrage (single-exchange, HFT-dominant)
  6) Perp-spot basis with funding combined edge

Only emits alerts when something NEW clears the bar (vs last run).
Always writes full state to logs/loop-latest.txt.
"""
from __future__ import annotations
import sys, os, time, json, hashlib
sys.path.insert(0, os.path.dirname(__file__))

from wt import funding_arb, funding_xex, alerts, spot_arb, triangular_arb, perp_spot_basis
from wt import hyperliquid_funding, stable_depeg, dex_cex_arb, options_rviv, kimchi_premium
from wt import prediction_market_arb, calendar_spread, curve_depeg, stat_arb
from wt.funding_arb import quarterly_basis_scan

STATE_FILE = os.path.join(os.path.dirname(__file__), "logs", "loop-state.json")
WATCHLIST = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
             "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "MATICUSDT",
             "LTCUSDT", "BCHUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT",
             "ARBUSDT", "OPUSDT", "INJUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT"]

def _sig(rows, key_fields):
    h = hashlib.sha1()
    for r in rows:
        s = "|".join(str(r.get(k, "")) for k in key_fields)
        h.update(s.encode())
    return h.hexdigest()

def _load_state():
    try:
        with open(STATE_FILE) as f: return json.load(f)
    except Exception: return {}

def _save_state(state):
    try:
        with open(STATE_FILE, "w") as f: json.dump(state, f, indent=2)
    except Exception: pass

def main():
    out_lines = []
    out_lines.append(f"=== LOOP SCAN {time.strftime('%Y-%m-%d %H:%M:%S %Z')} ===")

    # 1) Single-exchange funding arb
    try:
        fa_rows = funding_arb.scan(min_funding_pct_8h=0.01, min_quote_volume_m=10, min_spot_volume_m=2)
        out_lines.append("")
        out_lines.append(f"--- Funding arb (single-exchange, relaxed) — {len(fa_rows)} candidates ---")
        for r in fa_rows[:5]:
            out_lines.append(f"  {r['symbol']:12s} fr_8h={r['fr_pct']:+.4f}% basis={r['basis_pct']:+.3f}% "
                             f"net_24h={r['net_pct_24h']:+.3f}% APR={r['apr_pct']:+.1f}% ({r['direction']})")
    except Exception as e:
        out_lines.append(f"--- Funding arb scanner error: {e} ---")
        fa_rows = []

    # 2) Cross-exchange funding spread
    try:
        xe_rows, per_ex = funding_xex.scan()
        out_lines.append("")
        out_lines.append(f"--- Cross-exchange funding — {len(xe_rows)} candidates "
                         f"(exchanges: {sorted(per_ex.keys())}) ---")
        for r in xe_rows[:8]:
            out_lines.append(f"  {r['symbol']:12s} SHORT {r['high_ex']} ({r['high_fr']:+.4f}%) / "
                             f"LONG {r['low_ex']} ({r['low_fr']:+.4f}%) "
                             f"net_24h={r['net_pct_24h']:+.3f}% APR={r['apr_pct']:+.1f}%")
    except Exception as e:
        out_lines.append(f"--- Cross-exchange funding scanner error: {e} ---")
        xe_rows = []

    # 3) Order-book-verified spot arb on liquid watchlist
    try:
        sa_rows = spot_arb.scan(WATCHLIST, sizes_usdt=[5000, 25000])
        out_lines.append("")
        out_lines.append(f"--- Spot arb (order-book verified) — {len(sa_rows)} candidates ---")
        for r in sa_rows[:5]:
            out_lines.append(f"  {r['symbol']:12s} BUY {r['buy_ex']} -> SELL {r['sell_ex']} "
                             f"size=${r['size_usdt']:.0f} net={r['net_pct']:+.3f}%")
    except Exception as e:
        out_lines.append(f"--- Spot arb scanner error: {e} ---")
        sa_rows = []

    # 4) Quarterly futures basis (cash and carry)
    try:
        qb_rows = quarterly_basis_scan()
        out_lines.append("")
        out_lines.append(f"--- Quarterly basis (cash and carry) — {len(qb_rows)} candidates ---")
        for r in qb_rows[:6]:
            out_lines.append(f"  {r['symbol']:22s} basis={r['basis_pct']:+.3f}% days={r['days']} "
                             f"APR={r['apr_pct']:+.2f}% net_APR={r['net_apr_pct']:+.2f}% ({r['direction']})")
    except Exception as e:
        out_lines.append(f"--- Quarterly basis scanner error: {e} ---")
        qb_rows = []

    # 5) Triangular arbitrage (single-exchange, HFT-dominant)
    try:
        tri_rows = triangular_arb.scan(start_usdt=10000)
        out_lines.append("")
        out_lines.append(f"--- Triangular arb (Binance spot) — {len(tri_rows)} candidates ---")
        for r in tri_rows[:3]:
            out_lines.append(f"  {r['cycle']:35s} net={r['net_pct']:+.3f}% "
                             f"(start=${r['start_usdt']:.0f} -> end=${r['end_usdt']:.4f})")
    except Exception as e:
        out_lines.append(f"--- Triangular arb scanner error: {e} ---")
        tri_rows = []

    # 6) Perp-spot basis (single-exchange, lower-risk than cross-exchange)
    try:
        ps_rows = perp_spot_basis.scan()
        out_lines.append("")
        out_lines.append(f"--- Perp-spot basis (single-exchange) — {len(ps_rows)} candidates ---")
        for r in ps_rows[:6]:
            out_lines.append(f"  {r['symbol']:12s} basis={r['basis_pct']:+.3f}% fr_8h={r['fr_pct_8h']:+.4f}% "
                             f"net_24h={r['net_pct_24h']:+.3f}% APR={r['apr_pct']:+.1f}% ({r['direction']})")
    except Exception as e:
        out_lines.append(f"--- Perp-spot basis scanner error: {e} ---")
        ps_rows = []

    # 7) Hyperliquid funding (1h intervals, alts not on Binance)
    try:
        hl_rows, hl_err = hyperliquid_funding.scan()
        out_lines.append("")
        out_lines.append(f"--- Hyperliquid funding (1h interval) — {len(hl_rows)} candidates ---")
        if hl_err:
            out_lines.append(f"  error: {hl_err}")
        for r in hl_rows[:6]:
            out_lines.append(f"  {r['symbol']:14s} fr_1h={r['fr_pct_1h']:+.4f}% APR={r['apr_pct']:+.1f}% OI=\${r['oi_usd']/1e6:.1f}M")
    except Exception as e:
        out_lines.append(f"--- Hyperliquid funding scanner error: {e} ---")
        hl_rows = []

    # 8) Stablecoin depeg
    try:
        sd_rows = stable_depeg.scan()
        out_lines.append("")
        out_lines.append(f"--- Stablecoin depeg — {len(sd_rows)} candidates ---")
        for r in sd_rows[:6]:
            out_lines.append(f"  {r['symbol']:8s} avg=\${r['avg_price']:.5f} depeg={r['depeg_bps']:+.1f}bps "
                             f"(hi {r['hi_venue']} \${r['hi_price']:.5f} / lo {r['lo_venue']} \${r['lo_price']:.5f})")
    except Exception as e:
        out_lines.append(f"--- Stablecoin depeg scanner error: {e} ---")
        sd_rows = []

    # 9) DEX-CEX arbitrage (Uniswap V3 vs Binance)
    try:
        dc_rows = dex_cex_arb.scan(size_usdt=10000)
        out_lines.append("")
        out_lines.append(f"--- DEX-CEX arb (Uniswap V3 vs Binance) — {len(dc_rows)} candidates ---")
        for r in dc_rows[:5]:
            out_lines.append(f"  {r['symbol']:6s} binance=\${r['binance_px']:.4f} uniswap=\${r['uniswap_px']:.4f} "
                             f"spread={r['spread_bps']:+.1f}bps ({r['direction']})")
    except Exception as e:
        out_lines.append(f"--- DEX-CEX arb scanner error: {e} ---")
        dc_rows = []

    # 10) Options RV/IV edge
    try:
        ov_rows = options_rviv.scan()
        out_lines.append("")
        out_lines.append(f"--- Options RV/IV edge — {len(ov_rows)} candidates ---")
        for r in ov_rows[:6]:
            out_lines.append(f"  {r['symbol']:6s} RV={r['rv_pct']:.2f}% IV={r['iv_pct']:.2f}% edge={r['edge_pct']:+.2f}pp "
                             f"straddle=\${r['straddle_cost']:.2f} ({r['trade']})")
    except Exception as e:
        out_lines.append(f"--- Options RV/IV scanner error: {e} ---")
        ov_rows = []

    # 11) Kimchi premium (Korean vs US BTC)
    try:
        kp_rows, kp_err = kimchi_premium.scan()
        out_lines.append("")
        out_lines.append(f"--- Kimchi premium (Korean BTC vs Binance) — {len(kp_rows)} candidates ---")
        if kp_err:
            out_lines.append(f"  error: {kp_err}")
        for r in kp_rows[:4]:
            out_lines.append(f"  {r['venue']:14s} premium={r['premium_pct']:+.3f}% (KRW={r['local_price']:.0f} "
                             f"USD~=\${r['usd_equiv']:.2f} vs Binance \${r['binance_usd']:.2f})")
    except Exception as e:
        out_lines.append(f"--- Kimchi premium scanner error: {e} ---")
        kp_rows = []

    # 12) Prediction market arbitrage (Polymarket)
    try:
        pm_rows, pm_err = prediction_market_arb.scan()
        out_lines.append("")
        out_lines.append(f"--- Prediction market arb (Polymarket) --- {len(pm_rows)} candidates ---")
        if pm_err:
            out_lines.append(f"  error: {pm_err}")
        for r in pm_rows[:5]:
            out_lines.append(f"  {r['question'][:60]:60s} YES+NO={r['total']:.3f} edge={r['edge_pct']:+.2f}% vol=${r['volume_24h']:.0f}")
    except Exception as e:
        out_lines.append(f"--- Prediction market arb scanner error: {e} ---")
        pm_rows = []

    # 13) Calendar spread (Binance quarterlies)
    try:
        cs_rows = calendar_spread.scan()
        out_lines.append("")
        out_lines.append(f"--- Calendar spread (quarterlies) --- {len(cs_rows)} candidates ---")
        for r in cs_rows[:5]:
            out_lines.append(f"  {r['base']:10s} {r['near_sym']:22s} -> {r['far_sym']:22s} "
                             f"spread={r['spread_bps']:+.1f}bps APR={r['spread_apr_pct']:+.2f}% ({r['trade']})")
    except Exception as e:
        out_lines.append(f"--- Calendar spread scanner error: {e} ---")
        cs_rows = []

    # 14) Curve pool depeg
    try:
        cv_rows, cv_err = curve_depeg.scan()
        out_lines.append("")
        out_lines.append(f"--- Curve pool depeg --- {len(cv_rows)} candidates ---")
        if cv_err:
            out_lines.append(f"  error: {cv_err}")
        for r in cv_rows[:8]:
            out_lines.append(f"  {r['pool'][:30]:30s} {r['coin']:10s} price=${r['price']:.5f} depeg={r['depeg_bps']:+.1f}bps")
    except Exception as e:
        out_lines.append(f"--- Curve pool depeg scanner error: {e} ---")
        cv_rows = []

    # 15) Statistical arbitrage (cointegration)
    try:
        sa_rows = stat_arb.scan()
        out_lines.append("")
        out_lines.append(f"--- Stat arb (cointegration) --- {len(sa_rows)} candidates ---")
        for r in sa_rows[:6]:
            out_lines.append(f"  {r['asset_a']:10s} / {r['asset_b']:10s} beta={r['beta']:.3f} z={r['z_score']:+.2f} ({r['trade']})")
    except Exception as e:
        out_lines.append(f"--- Stat arb scanner error: {e} ---")
        sa_rows = []

    body = "\n".join(out_lines)
    print(body)

    # state + alerting
    state = _load_state()
    fa_sig = _sig(fa_rows, ["symbol", "direction"])
    xe_sig = _sig(xe_rows, ["symbol", "high_ex", "low_ex"])
    sa_sig = _sig(sa_rows, ["symbol", "buy_ex", "sell_ex"])
    new_fa = state.get("fa_sig") != fa_sig and fa_rows
    new_xe = state.get("xe_sig") != xe_sig and xe_rows
    new_sa = state.get("sa_sig") != sa_sig and sa_rows
    state.update({"fa_sig": fa_sig, "xe_sig": xe_sig, "sa_sig": sa_sig,
                  "last_run": time.strftime('%Y-%m-%d %H:%M:%S %Z')})
    _save_state(state)

    top_apr = max([r.get("apr_pct", 0) for r in (fa_rows + xe_rows + ps_rows + hl_rows)] + [0])
    if new_xe and top_apr > 25:
        top = [r for r in xe_rows if r.get("apr_pct", 0) >= 25][:3]
        msg = "NEW cross-exchange funding arb > 25% APR:\n\n" + "\n".join(
            f"  {r['symbol']}: SHORT {r['high_ex']}/{r['low_ex']} APR={r['apr_pct']:+.1f}%"
            for r in top)
        msg += "\n\nVerify live before trading. Research only."
        alerts.dispatch("NEW funding arb opportunity", msg)
        print("\n--- alert dispatched ---")
    elif new_fa and top_apr > 25:
        top = [r for r in fa_rows if r.get("apr_pct", 0) >= 25][:3]
        msg = "NEW single-exchange funding arb > 25% APR:\n\n" + "\n".join(
            f"  {r['symbol']}: {r['direction']} APR={r['apr_pct']:+.1f}%"
            for r in top)
        msg += "\n\nVerify live before trading. Research only."
        alerts.dispatch("NEW funding arb opportunity", msg)
        print("\n--- alert dispatched ---")
    elif new_sa and sa_rows:
        msg = "NEW order-book-verified spot arb:\n\n" + "\n".join(
            f"  {r['symbol']}: BUY {r['buy_ex']} -> SELL {r['sell_ex']} "
            f"size=${r['size_usdt']:.0f} net={r['net_pct']:+.3f}%"
            for r in sa_rows[:3])
        alerts.dispatch("NEW spot arb opportunity", msg)
        print("\n--- alert dispatched ---")

    # Kimchi premium alert (signal-grade, not pure arb unless you have Korean KYC)
    if kp_rows and any(abs(r["premium_bps"]) > 100 for r in kp_rows):
        big = [r for r in kp_rows if abs(r["premium_bps"]) > 100][:2]
        msg = "Large kimchi premium detected (>100bps):\n\n" + "\n".join(
            f"  {r['venue']}: {r['premium_pct']:+.3f}% vs Binance"
            for r in big)
        msg += "\n\nSignal: Korean retail sentiment. Not pure arb unless you have Korean KYC."
        alerts.dispatch("Kimchi premium signal", msg)
        print("\n--- kimchi alert dispatched ---")

    return 0

if __name__ == "__main__":
    sys.exit(main())
