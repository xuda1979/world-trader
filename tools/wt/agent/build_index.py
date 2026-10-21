#!/usr/bin/env python3
"""Build results/equity_research/INDEX.md from all report JSONs.

Ranks covered names by the judge's base-case 12-mo price target (the
report's own estimate of expected return). Re-run after any batch:
    python tools/wt/agent/build_index.py
"""
from __future__ import annotations
import glob, json, os

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))),
    "results", "equity_research")

RATING_ORDER = {"BUY": 0, "OVERWEIGHT": 1, "HOLD": 2, "UNDERWEIGHT": 3, "SELL": 4}


def _pct(x) -> str:
    if x is None:
        return "n/a"
    return f"{x * 100:+.1f}%"


def _latest_json_per_sym() -> list:
    """All report JSONs, keeping only the newest date per symbol."""
    files = {}
    for f in glob.glob(os.path.join(OUT_DIR, "*.json")):
        name = os.path.basename(f)
        if "_" not in name or not name.endswith(".json"):
            continue
        sym, date = name.rsplit("_", 1)[0], name.rsplit("_", 1)[1][:-5]
        if sym == "INDEX" or sym == "TOP":
            continue
        if sym not in files or date > files[sym][0]:
            files[sym] = (date, f)
    return [f for _, f in sorted(files.values())]


def main() -> int:
    rows = []
    for f in _latest_json_per_sym():
        d = json.load(open(f))
        j = d.get("judge") or {}
        sc = j.get("scenarios") or {}
        base = sc.get("base") or {}
        bull = sc.get("bull") or {}
        bear = sc.get("bear") or {}
        price = d.get("price")
        base_pt = base.get("pt")
        exp_ret = (base_pt / price - 1.0) if (base_pt and price) else None
        rows.append({
            "sym": d["sym"], "date": f.rsplit("_", 1)[-1].replace(".json", ""),
            "price": price, "rating": j.get("rating") or "n/a",
            "conv": j.get("conviction"), "convg": j.get("convergence"),
            "base_pt": base_pt, "exp_ret": exp_ret,
            "bull_pt": bull.get("pt"), "bear_pt": bear.get("pt"),
            "rationale": (j.get("decision_rationale") or "")[:140],
            "fair": ((d.get("valuation") or {}).get("outputs") or {})
                .get("fair_value"),
            "errors": len(d.get("errors") or []),
        })

    rows.sort(key=lambda r: (-(r["exp_ret"] if r["exp_ret"] is not None
                                else -999), RATING_ORDER.get(r["rating"], 9)))

    L = ["# Equity research coverage — index (agent debate reports)", ""]
    L.append(f"*{len(rows)} names covered. Ranks by the judge's base-case "
             f"12-mo target vs last price = the report's expected-return "
             f"estimate. Updated {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')} "
             f"UTC. Research only; not investment advice.*")
    L.append("")

    # Top picks: names with a real positive expected-return signal (base PT
    # above price) AND a forward-EPS valuation anchor.
    picks = [r for r in rows
             if r["exp_ret"] is not None and r["exp_ret"] > 0.02
             and (r["fair"] or {}).get("base")]
    if picks:
        L.append("## Top picks (positive expected return, forward-EPS anchor)")
        L.append("")
        for r in picks:
            L.append(f"- **{r['sym']}** — {r['rating']} ({r['conv']}), base PT "
                     f"{r['base_pt']} → **{_pct(r['exp_ret'])}** vs price "
                     f"{r['price']}; bear-case PT {r['bear_pt']} caps the "
                     f"downside scenario.")
        L.append("")
        L.append("> Caveat: single-run LLM ratings vary between runs (e.g. "
                 "MU was BUY then HOLD). The durable output is the "
                 "evidence-graded debate in each report.")
        L.append("")
    L.append("| Rank | Sym | Current price | Predicted 1-yr price | ExpRet→ | Rating | Conv | Bear PT | Convergence |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        L.append(
            f"| {i} | **{r['sym']}** | {r['price'] or 'n/a'} | "
            f"{r['base_pt'] or 'n/a'} | {_pct(r['exp_ret'])} | "
            f"{r['rating']} | {r['conv'] or 'n/a'} | "
            f"{r['bear_pt'] or 'n/a'} | {'yes' if r['convg'] else 'no'} |")
    L.append("")
    L.append("## Rationales (judge)")
    for r in rows:
        L.append(f"- **{r['sym']}** — {r['rationale']}")
    L.append("")
    L.append("## Notes")
    L.append("- Screening: top names by 12-mo Sharpe on the repo's US price "
             "panel, diversified across sectors.")
    L.append("- Base PT = judge's 12-mo base-case target, anchored to the "
             "deterministic valuation where available (see per-report "
             "valuation notes for basis: forward vs trailing EPS).")
    L.append("- Convergence 'no' means the bull/bear debate was genuinely "
             "unresolved — treat those ratings as lower-confidence.")
    L.append("- Full reports: `results/equity_research/<SYM>_<date>.md` "
             "(JSON alongside).")
    L.append("")

    path = os.path.join(OUT_DIR, "INDEX.md")
    with open(path, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {path} ({len(rows)} names)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
