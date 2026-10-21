#!/usr/bin/env python3
"""world-trader AI agent CLI.

One-command multi-agent trading analysis. Runs the full pipeline:
  analysts -> bull/bear -> 3-way risk debate -> research manager ->
  risk manager -> trader -> reflector

Usage:
  python tools/agent_cli.py                  # auto-pick top candidate
  python tools/agent_cli.py --sym AAPL       # focus on a ticker
  python tools/agent_cli.py --sym 600519.SS  # China A-share
  python tools/agent_cli.py --sym BTC-USD    # crypto
  python tools/agent_cli.py --no-arbs        # skip arb probe
  python tools/agent_cli.py --json           # machine-readable output
  python tools/agent_cli.py --doctor         # self-check (providers, tools)

Environment:
  XAI_API_KEY        -- xAI Grok (preferred; cheap + fast)
  ANTHROPIC_API_KEY  -- Anthropic Claude (fallback)

This is a research tool. Nothing here is financial advice. Markets move
fast; verify live prices before acting.
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

# Ensure tools/ is on sys.path so `from wt.agent import ...` works
_TOOLS_DIR = Path(__file__).resolve().parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from wt.agent import run_agent, TOOLS, list_tools  # noqa: E402
from wt.agent.orchestrator import render_result_text  # noqa: E402
from wt.agent.llm_chat import available_provider, probe_llm  # noqa: E402


def _doctor() -> int:
    print("[agent] self-check")
    p = available_provider()
    print(f"  LLM provider: {p or 'NONE (need XAI_API_KEY or ANTHROPIC_API_KEY)'}")
    print(f"  tools registered: {len(TOOLS)}")
    for t in list_tools():
        print(f"    - {t}")
    # Try to import every wt module the tools depend on
    print("\n[wt modules] import test:")
    from wt import core
    for m in ("report", "deepdive", "breaking", "llm", "markets",
              "funding_arb", "spot_arb", "triangular_arb", "dex_cex_arb",
              "perp_spot_basis", "stable_depeg", "curve_depeg",
              "calendar_spread", "kimchi_premium", "prediction_market_arb",
              "defi_rate_arb", "rv_setups", "stat_arb", "country_crisis",
              "hyperliquid_funding"):
        try:
            __import__("wt." + m, fromlist=["_"])
            print(f"  OK    wt.{m}")
        except Exception as e:
            print(f"  FAIL  wt.{m}  ({core.describe_err(e)})")
    return 0 if p else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="world-trader AI agent -- multi-agent debate -> trade ticket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    ap.add_argument("--sym", default=None,
                    help="ticker to analyze (default: auto-pick top scan row)")
    ap.add_argument("--no-arbs", action="store_true",
                    help="skip the cross-arb probe")
    ap.add_argument("--scan-only", action="store_true",
                    help="skip LLM debate; return only the scan + arbs. "
                         "Useful when no LLM provider is available, or for "
                         "a fast 'what does the scanner see' check.")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of text")
    ap.add_argument("--doctor", action="store_true",
                    help="run self-check and exit")
    ap.add_argument("--probe-llm", action="store_true",
                    help="test every configured LLM provider and exit")
    ap.add_argument("--report", metavar="SYM", default=None,
                    help="generate an equity research report for SYM via "
                         "agent debate (bull/bear/rebuttals/judge) instead "
                         "of a trade ticket")
    ap.add_argument("--watchlist", metavar="A,B,C", default=None,
                    help="with --report: cover several tickers in sequence")
    ap.add_argument("--force", action="store_true",
                    help="with --report: regenerate today's report if it "
                         "already exists")
    args = ap.parse_args()

    if args.doctor:
        return _doctor()

    if args.probe_llm:
        print("[agent] probing LLM providers...")
        result = probe_llm()
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("recommended") else 2

    if args.report or args.watchlist:
        from wt.agent.research_report import generate_report, generate_watchlist
        if args.watchlist:
            tickers = [s.strip().upper() for s in args.watchlist.split(",")
                       if s.strip()]
            if not tickers:
                print("ERROR: empty watchlist", file=sys.stderr)
                return 2
            results = generate_watchlist(tickers, force=args.force)
        else:
            results = [generate_report(args.report.upper(), force=args.force)]
        if args.json:
            print(json.dumps([r.as_dict() for r in results], indent=2,
                             default=str))
        else:
            for r in results:
                if r.report_path:
                    print(f"[research-report] {r.sym} -> {r.report_path}")
                if r.errors:
                    print(f"[research-report] {r.sym} errors:")
                    for e in r.errors:
                        print(f"    - {e}")
        return 0

    if available_provider() is None and not args.scan_only:
        print("ERROR: no LLM provider configured. Set XAI_API_KEY or "
              "ANTHROPIC_API_KEY, or use --scan-only for a no-LLM scan.",
              file=sys.stderr)
        print("Run with --doctor for the full self-check.", file=sys.stderr)
        return 2

    mode = "scan-only" if args.scan_only else "full-debate"
    print(f"[agent] running multi-agent pipeline "
          f"(sym={args.sym or 'auto'}, mode={mode})...", file=sys.stderr)
    res = run_agent(sym=args.sym, include_arbs=not args.no_arbs,
                    scan_only=args.scan_only)

    if args.json:
        print(json.dumps(res.as_dict(), indent=2, default=str))
    else:
        print(render_result_text(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
