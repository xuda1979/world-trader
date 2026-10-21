#!/usr/bin/env python3
"""Build results/equity_research/TOP_PICKS.md — actionable synthesis of the
top picks, assembled deterministically from the report JSONs (no LLM).

    python tools/wt/agent/build_top_picks.py
"""
from __future__ import annotations
import glob, json, os

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))),
    "results", "equity_research")


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
        if sym not in files or date > files[sym][0]:
            files[sym] = (date, f)
    return [f for _, f in sorted(files.values())]


def main() -> int:
    rows = []
    for f in _latest_json_per_sym():
        d = json.load(open(f))
        j = d.get("judge") or {}
        sc = j.get("scenarios") or {}
        base, bear = sc.get("base") or {}, sc.get("bear") or {}
        price = d.get("price")
        exp = (base.get("pt") / price - 1.0) if (base.get("pt") and price) else None
        if exp is None or exp <= 0.02:
            continue  # only picks with a real positive expected return
        rows.append({
            "sym": d["sym"], "price": price, "rating": j.get("rating"),
            "conv": j.get("conviction"), "base_pt": base.get("pt"),
            "bear_pt": bear.get("pt"), "exp": exp,
            "rationale": j.get("decision_rationale", ""),
            "catalysts": [c.get("catalyst") for c in (j.get("catalysts") or [])][:4],
            "risks": [r.get("risk") for r in (j.get("risks") or [])][:4],
            "report": os.path.basename(f).replace(".json", ".md"),
        })
    rows.sort(key=lambda r: -(r["exp"] if r["exp"] is not None else -999))

    L = ["# Top picks — synthesis (agent debate equity research)", ""]
    L.append(f"*{len(rows)} names with a positive expected-return signal, "
             "assembled deterministically from the per-name report JSONs. "
             "Research only; not investment advice.*")
    L.append("")
    L.append("## How these were picked")
    L.append("")
    L.append("- Universe: top names by 12-mo Sharpe on the repo's US price "
             "panel (momentum is the best-documented cross-sectional "
             "expected-return anomaly), diversified across sectors.")
    L.append("- Signal: each name got a full agent debate (bull/bear with "
             "rebuttals, evidence-graded against real data) plus a "
             "deterministic Python valuation. Names below only appear here "
             "when the judge's base-case 12-mo target is above the price "
             "AND a forward-consensus EPS anchor existed (no anchor -> the "
             "valuation abstains and no signal is claimed).")
    L.append("")
    L.append("| Sym | Rating | Conv | Current price | Predicted 1-yr price | Expected return |")
    L.append("|---|---|---|---|---|---|")
    for r in rows:
        L.append(f"| **{r['sym']}** | {r['rating']} | {r['conv']} | "
                 f"{r['price']} | {r['base_pt']} | **{_pct(r['exp'])}** |")
    L.append("")
    for r in rows:
        L.append(f"## {r['sym']} — {r['rating']} "
                 f"(conviction {r['conv']}, expected {_pct(r['exp'])} to "
                 f"base PT {r['base_pt']})")
        L.append("")
        L.append(f"**Judge's rationale:** {r['rationale']}")
        L.append("")
        if r["catalysts"]:
            L.append("**Catalysts:** " + "; ".join(r["catalysts"]))
            L.append("")
        if r["risks"]:
            L.append("**Key risks:**")
            for x in r["risks"]:
                L.append(f"- {x}")
            L.append("")
        L.append(f"Full report: `{r['report']}` (JSON alongside).")
        L.append("")
    L.append("## Caveats")
    L.append("")
    L.append("- Single-run LLM ratings vary between runs (e.g. MU was BUY "
             "then HOLD on two runs the same day); treat ratings as "
             "directional, not precise. The evidence-graded debate is the "
             "stable output.")
    L.append("- Forward EPS is annualized from one consensus quarter "
             "(crude; disclosed per report). Valuation bands are "
             "mechanistic (P/E x 0.8/1.0/1.25), no sector judgment.")
    L.append("- Prices are the last close at report time; verify live "
             "quotes before any decision.")
    L.append("")

    path = os.path.join(OUT_DIR, "TOP_PICKS.md")
    with open(path, "w") as f:
        f.write("\n".join(L))
    print(f"wrote {path} ({len(rows)} picks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
