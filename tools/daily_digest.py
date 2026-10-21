#!/usr/bin/env python3
"""Daily digest: run funding-arb + cross-exchange scanners, ship summary.

Designed to run daily at 09:00 local via launchd. Pushes a digest to all
configured alert channels (email/Telegram/Discord) and always logs locally.

Usage:
  python3 tools/daily_digest.py
"""
from __future__ import annotations
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(__file__))

from wt import alerts
from wt import funding_arb
from wt import funding_xex

def fmt_pct(x): return f"{x:+.3f}%"

def build_digest():
    parts = []
    parts.append(f"world-trader daily digest  {time.strftime('%Y-%m-%d %H:%M %Z')}")
    parts.append("")
    parts.append("=== FUNDING ARB (single-exchange spot-vs-perp) ===")
    try:
        rows = funding_arb.scan()
        if not rows:
            parts.append("  no candidates cleared the bar.")
        else:
            parts.append(f"  {len(rows)} candidates:")
            for r in rows[:10]:
                parts.append(
                    f"  - {r['symbol']:12s} fr_8h={fmt_pct(r['fr_pct'])} "
                    f"basis={fmt_pct(r['basis_pct'])} net_24h={fmt_pct(r['net_pct_24h'])} "
                    f"APR={fmt_pct(r['apr_pct'])} ({r['direction']})"
                )
    except Exception as e:
        parts.append(f"  scanner error: {e}")
        parts.append(traceback.format_exc())

    parts.append("")
    parts.append("=== CROSS-EXCHANGE FUNDING SPREAD ===")
    try:
        rows, per_ex = funding_xex.scan()
        parts.append("  exchanges: " + ", ".join(f"{e}={len(r)}" for e, r in per_ex.items()))
        if not rows:
            parts.append("  no cross-exchange spread cleared the bar.")
        else:
            parts.append(f"  {len(rows)} candidates:")
            for r in rows[:10]:
                parts.append(
                    f"  - {r['symbol']:12s} SHORT {r['high_ex']} ({fmt_pct(r['high_fr'])}) / "
                    f"LONG {r['low_ex']} ({fmt_pct(r['low_fr'])}) "
                    f"spread_8h={fmt_pct(r['spread_pct_8h'])} net_24h={fmt_pct(r['net_pct_24h'])} "
                    f"APR={fmt_pct(r['apr_pct'])}"
                )
    except Exception as e:
        parts.append(f"  scanner error: {e}")
        parts.append(traceback.format_exc())

    parts.append("")
    parts.append("=== RISK REMINDER ===")
    parts.append("  Funding arbs are delta-neutral but have real risks:")
    parts.append("  - funding interval mismatch (4h vs 8h) between exchanges")
    parts.append("  - liquidation if margin imbalance grows")
    parts.append("  - withdrawal delays / exchange outages")
    parts.append("  - small-cap symbols may have wide spreads / thin liquidity")
    parts.append("  Verify live before trading. Research only, not financial advice.")
    return "\n".join(parts)

def main():
    body = build_digest()
    print(body)
    print("\n--- dispatching to alert channels ---")
    res = alerts.dispatch("world-trader daily digest", body)
    import json
    print(json.dumps(res, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
