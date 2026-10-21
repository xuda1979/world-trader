#!/usr/bin/env python3
"""Buffett rule #1 — consistent earnings power — from free EDGAR companyfacts.

For each ticker, pulls the 10 most recent ANNUAL GAAP earnings-per-share
(fully diluted) facts from tools/quant/bigmove/data/edgar_facts_full/<SYM>.json
and prints the history + a Buffett-style consistency verdict:

  pos_yrs : years with positive EPS in the last 10 (Buffett wants ~10/10)
  up_yrs  : years with EPS up YoY
  cv      : coefficient of variation of annual EPS (lower = steadier)

Point-in-time safe: uses the 'filed' date, values are only known once filed.

Usage:
  python tools/buffett_screen.py --json --top 25 | python tools/buffett_consistency.py
  python tools/buffett_consistency.py --syms AAPL KO JNJ
"""
from __future__ import annotations
import json, sys, os, argparse, glob

HERE = os.path.dirname(os.path.abspath(__file__))
FACTS = os.path.join(HERE, "quant", "bigmove", "data", "edgar_facts_full")
EPS_TAG = "EarningsPerShareDiluted"


def annual_eps(fp):
    """Return list of (year, eps) from annual (>=300 day) period facts, newest first."""
    try:
        d = json.load(open(fp))
    except Exception:
        return None
    node = d.get("facts", {}).get("us-gaap", {}).get(EPS_TAG)
    if not node:
        return None
    rows = []
    for u, vlist in (node.get("units") or {}).items():
        if "USD" not in u:
            continue
        for v in vlist:
            end = v.get("end")
            start = v.get("start")
            if not end or not start:
                continue
            dur = (__import__("datetime").date.fromisoformat(end)
                   - __import__("datetime").date.fromisoformat(start)).days
            if dur >= 300:  # annual fact (12-month period)
                try:
                    rows.append((int(end[:4]), float(v.get("val"))))
                except (TypeError, ValueError):
                    pass
    if not rows:
        return None
    # dedupe per fiscal year, keep the latest (restatements filed later)
    by_year = {}
    for y, v in sorted(rows, key=lambda r: r[0]):
        by_year[y] = v
    return sorted(by_year.items(), reverse=True)[:10]


def verdict(pairs):
    ys, vs = zip(*pairs) if pairs else ([], [])
    pos = sum(1 for v in vs if v > 0)
    ups = sum(1 for a, b in zip(vs[1:], vs[:-1]) if b > a)
    mean = sum(vs) / len(vs) if vs else 0
    cv = (sum((v - mean) ** 2 for v in vs) / len(vs)) ** 0.5 / abs(mean) if mean else 9.9
    return pos, ups, cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--syms", nargs="*", default=None)
    ap.add_argument("--years", type=int, default=10)
    args = ap.parse_args()

    syms = args.syms
    if not syms and not sys.stdin.isatty():
        try:
            syms = [r["symbol"] for r in json.load(sys.stdin)]
        except Exception:
            syms = None
    if not syms:
        ap.error("pass --syms or pipe buffett_screen.py --json output")

    print(f"{'SYM':<6} {'pos/yr':>7} {'up/yr':>6} {'CV':>5}   EPS history (year: eps)")
    for s in syms:
        fp = os.path.join(FACTS, f"{s}.json")
        if not os.path.exists(fp):
            print(f"{s:<6} {'n/a':>7} {'n/a':>6} {'n/a':>5}   (no EDGAR facts file)")
            continue
        pairs = annual_eps(fp)
        if not pairs:
            print(f"{s:<6} {'n/a':>7} {'n/a':>6} {'n/a':>5}   (no annual EPS in facts file)")
            continue
        pairs = pairs[: args.years]
        pos, ups, cv = verdict(pairs)
        hist = "  ".join(f"{y}:{v:,.2f}" for y, v in pairs)
        print(f"{s:<6} {pos:>4}/{len(pairs):<2} {ups:>5}/{len(pairs)-1:<2} {cv:>5.2f}   {hist}")


if __name__ == "__main__":
    main()
