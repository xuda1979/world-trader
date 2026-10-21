#!/usr/bin/env python3
"""Print the top-20 equity research universe as a clean table:
   current price | predicted one-year-later price | expected return.
Pulls only from the latest report JSONs (no LLM). Ranks by expected return.
    python tools/wt/agent/print_expected_returns.py
"""
from __future__ import annotations
import glob, json, os

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))),
    "results", "equity_research")


def _latest_json_per_sym() -> list:
    files = {}
    for f in glob.glob(os.path.join(OUT_DIR, "*.json")):
        name = os.path.basename(f)
        if "_" not in name or not name.endswith(".json"):
            continue
        sym, date = name.rsplit("_", 1)[0], name.rsplit("_", 1)[1][:-5]
        if sym not in files or date > files[sym][0]:
            files[sym] = (date, f)
    return [f for _, f in sorted(files.values())]


def _pct(x) -> str:
    return "n/a" if x is None else f"{x * 100:+.1f}%"


def main() -> int:
    rows = []
    for f in _latest_json_per_sym():
        d = json.load(open(f))
        j = d.get("judge") or {}
        base = (j.get("scenarios") or {}).get("base") or {}
        price = d.get("price")
        pt = base.get("pt")
        exp = (pt / price - 1.0) if (pt and price) else None
        rows.append((d["sym"], price, pt, exp, j.get("rating")))
    rows.sort(key=lambda r: -(r[3] if r[3] is not None else -999))

    print(f"{'Sym':<6}{'Current':>12}{'Pred-1yr':>12}{'ExpRet':>10}  Rating")
    print("-" * 52)
    for sym, price, pt, exp, rating in rows:
        cur = f"{price or 'n/a':>12}"
        pred = f"{pt or 'n/a':>12}"
        print(f"{sym:<6}{cur}{pred}{_pct(exp):>10}  {rating or 'n/a'}")
    print("-" * 52)
    n_anchor = sum(1 for r in rows if r[3] is not None)
    print(f"{len(rows)} names covered; {n_anchor} have a forward-EPS-anchored "
          f"predicted 1-yr price (the rest abstain - no free consensus data).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
