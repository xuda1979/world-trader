"""Agent debate -> EQUITY RESEARCH REPORT (not a trade ticket).

Extends the repo's multi-agent debate architecture (orchestrator.py) to
produce sell-side-style research reports. Architecture ideas adapted from
projects evaluated on 2026-08-22 (full citation list in RESEARCH_NOTES.md,
tier 2 additions):

- AlphaAnalyst (kbhujbal/AlphaAnalyst): schema-validated research memo;
  "the LLM is a writer, not a knower" -- every number is computed in
  Python from real data, the LLM only writes prose over those numbers.
- StockSense-AI (Spkap/StockSense-AI): anti-sycophancy debate mechanics --
  bull sees growth-positive data first, bear sees risk data first;
  mandatory rebuttal round; every claim is evidence-graded against the
  actual data sections.
- FinAgent (helloJamest/FinAgent): judge node with convergence detection
  and multi-criteria scoring.
- ai-hedge-fund v2 (virattt/ai-hedge-fund): PIT-honesty -- the LLM never
  touches the numbers; missing data => abstain, never fabricate.
- FINSABER / deeplearning-wisc/debate-or-vote (papers): debate only adds
  value over independent voting when claims are grounded and checked --
  hence the rule-based evidence-grading pass.

Pipeline (stdlib-only, mirrors the repo's agent conventions):

  gather data -> bull / bear (anti-sycophancy data ordering)
              -> rebuttal round (each side answers the other's claims)
              -> evidence grading (rule-based, against real data)
              -> deterministic valuation (pure Python, no LLM)
              -> judge (convergence, rating, scenarios, price targets)
              -> report writer (deterministic Markdown assembly)

Every node degrades gracefully and returns None on failure -- the report
is built from whatever steps succeeded. Nothing here places orders; this
is research only.
"""
from __future__ import annotations
import json, os, re, sys, time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .llm_chat import chat, parse_json_response, available_provider

# ---------------------------------------------------------------------------
# Output location
# ---------------------------------------------------------------------------

DEFAULT_OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))),
    "results", "equity_research")


@dataclass
class ReportResult:
    """Structured result of one equity-research report generation."""
    sym: str = ""
    generated_utc: str = ""
    price: Optional[float] = None
    data_sections: List[str] = field(default_factory=list)
    bull: Optional[Dict[str, Any]] = None
    bear: Optional[Dict[str, Any]] = None
    rebuttals: Dict[str, Any] = field(default_factory=dict)
    grading: Dict[str, Any] = field(default_factory=dict)
    valuation: Optional[Dict[str, Any]] = None
    judge: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    elapsed_sec: float = 0.0
    report_path: Optional[str] = None
    json_path: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "sym": self.sym,
            "generated_utc": self.generated_utc,
            "price": self.price,
            "data_sections": self.data_sections,
            "bull": self.bull,
            "bear": self.bear,
            "rebuttals": self.rebuttals,
            "grading": self.grading,
            "valuation": self.valuation,
            "judge": self.judge,
            "errors": self.errors,
            "elapsed_sec": round(self.elapsed_sec, 2),
            "report_path": self.report_path,
            "json_path": self.json_path,
        }


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------

_SECTION_LABELS = {
    "quote": "current price/last close",
    "technicals": "20/50/200-day moving averages and trend",
    "news": "recent headlines with sources and timestamps",
    "catalyst": "next scheduled catalyst (earnings/FDA/IPO/dividend) with consensus estimates",
    "analyst": "analyst recommendation breakdown (strong_buy/buy/hold/sell counts, score)",
    "analyst_target": "analyst price targets if available",
    "insider": "recent insider transactions (buys/sells, net shares)",
    "earnings": "recent quarterly EPS actuals vs estimates with surprise %",
    "fundamentals": "valuation & quality: market cap, P/E, P/B, P/S, ROE, debt/equity, 52w range",
    "filings": "recent SEC filings (8-K etc.)",
    "peers": "peer ticker list",
    "clusters": "theme clusters the stock belongs to",
    "hn_mentions": "Hacker News mention count",
    "gdelt_tone": "GDELT news tone score",
}


def _gather(sym: str) -> Dict[str, Any]:
    """Gather every available data signal on the ticker (no LLM needed)."""
    from wt import deepdive, catalysts
    out = deepdive.gather(sym, want_llm=False)
    data = out.get("data") or out
    if not isinstance(data, dict) or not data.get("sym"):
        data = {"sym": sym}
    # The gather's catalyst window is 30 days; widen to 90 so names whose
    # next earnings lands a quarter out still get a forward-consensus EPS
    # (the report's deterministic valuation needs it). Keep the narrower
    # result if the wide look fails.
    wide = catalysts.catalyst_for(sym, days=90)
    if wide and not (data.get("catalyst") or {}).get("eps_est"):
        data["catalyst"] = wide
    # Prune: keep only sections the report uses, so LLM prompts stay tight.
    keep = set(_SECTION_LABELS) | {"sym", "peers", "clusters"}
    pruned = {}
    for k in ("sym", "peers", "clusters"):
        if data.get(k) is not None:
            pruned[k] = data[k]
    for k in _SECTION_LABELS:
        if data.get(k) is not None:
            pruned[k] = data[k]
    return pruned


# ---------------------------------------------------------------------------
# Data rendering for the LLM (anti-sycophancy ordering)
# ---------------------------------------------------------------------------

def _fmt_section(name: str, value: Any) -> str:
    try:
        s = json.dumps(value, indent=0, default=str)
    except Exception:
        s = str(value)
    if len(s) > 1400:  # keep prompts bounded; truncate the tail
        s = s[:1400] + "...<truncated>"
    return f"[{name}] {_SECTION_LABELS.get(name, '')}\n{s}"


def _data_view(sym: str, data: Dict[str, Any], side: str) -> str:
    """Render the data for one side.

    Anti-sycophancy ordering (StockSense-AI): the BULL sees the
    growth-positive sections first and the risk sections last; the BEAR
    sees the opposite ordering. The content is identical.
    """
    growth = ["analyst", "analyst_target", "catalyst", "earnings",
              "fundamentals", "news", "gdelt_tone", "hn_mentions"]
    risk = ["insider", "filings", "technicals", "quote"]
    if side == "bull":
        order = growth + risk
    else:
        order = risk + growth
    parts = [f"TICKER: {sym}", f"ROLE: {side.upper()} case"]
    for k in order:
        if k in data:
            parts.append(_fmt_section(k, data[k]))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# LLM node helpers
# ---------------------------------------------------------------------------

def _repair_truncated_json(text: Optional[str]) -> Optional[dict]:
    """Deterministic repair for responses cut off mid-JSON.

    The LLM (esp. fast models) occasionally stops mid-list, e.g.
    `... "strength": 0.8}` instead of `... "strength": 0.8}]}`. The first
    object is usually complete, so appending the missing closers recovers
    the payload with zero extra LLM cost. Only ever appends; never edits.
    """
    p = parse_json_response(text)
    if p is not None:
        return p
    if not text:
        return None
    for suffix in ("]}", "}]}", "]}", "]}]}", "}}", "]}}", '"}'):
        try:
            cand = text.strip() + suffix
            a, b = cand.find("{"), cand.rfind("}")
            if a >= 0 and b > a:
                d = json.loads(cand[a:b + 1])
                if isinstance(d, dict):
                    return d
        except (json.JSONDecodeError, ValueError):
            continue
    return None


def _llm_json(system_prompt: str, user_prompt: str, errors: List[str],
              label: str, strong: bool = False) -> Optional[dict]:
    """Standard node pattern: LLM -> JSON, log errors, never raise."""
    if available_provider() is None:
        errors.append(f"{label}: no LLM provider configured (need "
                      "XAI_API_KEY or ANTHROPIC_API_KEY)")
        return None
    raw = chat(system_prompt, user_prompt, strong=strong,
               temperature=0.3, max_tokens=2200,
               disable_thinking=True)
    if not raw:
        errors.append(f"{label}: LLM returned empty")
        return None
    parsed = _repair_truncated_json(raw)
    if parsed is None:
        # Still broken after repair: retry once with a larger budget. (A
        # brevity hint made this worse on deepseek-flash -- plain retry.)
        raw = chat(system_prompt, user_prompt, strong=strong,
                   temperature=0.3, max_tokens=4000,
                   disable_thinking=True)
        parsed = _repair_truncated_json(raw)
        if parsed is None:
            errors.append(f"{label}: failed to parse JSON (first 200 chars: "
                          f"{raw[:200]!r})" if raw else
                          f"{label}: retry returned empty")
            return None
    return parsed


_RESEARCHER_SYSTEM = (
    "You are the {side} case researcher for an equity research report. "
    "Your job is to argue the strongest honest {side} case for the ticker, "
    "based ONLY on the data provided. Rules:\n"
    "1. Every claim MUST be grounded in a specific data field. Cite it in "
    "the 'evidence' field as <section>.<field>, e.g. "
    "'fundamentals.pe_ttm' or 'catalyst.eps_est' or 'earnings.surprise_pct'.\n"
    "2. If the data does not support a claim, do NOT make it. Missing data "
    "is a reason to stay silent or to say so explicitly.\n"
    "3. Do not hedge: this is your side's case. Pick the 4-6 strongest "
    "claims. No filler.\n"
    "4. Return ONLY the JSON object:\n"
    '{"stance": "bullish|bearish", "confidence": <0-1>, '
    '"claims": [{"claim": "<one sentence>", "evidence": "<section.field>", '
    '"impact": "positive|negative"}]}'
)

_REBUTTAL_SYSTEM = (
    "You are the {side} researcher responding to the OPPOSING case. "
    "Address each of the opposing side's claims head-on. For each one: "
    "either concede it, or rebut it using a specific counter-field from "
    "the data (evidence as <section>.<field>), or point out the inference "
    "gap. Be specific and numerical. Return ONLY:\n"
    '{"rebuttals": [{"target_claim": "<the claim you are answering>", '
    '"response": "<your counter-argument, 1-2 sentences>", '
    '"counter_evidence": "<section.field or null>", '
    '"concede": true|false, "strength": <0-1>}]}'
)

_JUDGE_SYSTEM = (
    "You are the head of a sell-side equity research team. You have read "
    "the bull case, the bear case, their rebuttals, the evidence grading, "
    "and a deterministic valuation computed in Python (never modify its "
    "numbers). Produce the final verdict.\n"
    "Rules:\n"
    "1. Scenarios: bull/base/bear 12-month price targets and probabilities. "
    "Base-case target MUST stay within +-25% of the deterministic "
    "valuation's base fair value when one exists. Probabilities must sum "
    "to 1.0.\n"
    "2. Rating scale: BUY / OVERWEIGHT / HOLD / UNDERWEIGHT / SELL.\n"
    "3. In the 'catalysts' list, when the data's 'catalyst' section has an "
    "explicit date (e.g. next earnings date), use it as the date; otherwise "
    "'unknown'.\n"
    "4. Convergence detection: if bull and bear largely agree on direction "
    "(or disagree on nothing material), set convergence true and keep "
    "conviction; if the debate is unresolved, convergence false and lower "
    "conviction.\n"
    "4. All facts must reference the data already gathered; no new "
    "facts.\n"
    'Return ONLY JSON: {"convergence": true|false, "rating": "<RATING>", '
    '"conviction": <0-1>, "scenarios": {"bull": {"prob": <0-1>, "pt": '
    '<number>, "thesis": "<1 sentence>"}, "base": {...}, "bear": {...}}, '
    '"catalysts": [{"catalyst": "<item>", "date": "<when or unknown>", '
    '"impact": "positive|negative"}], "risks": [{"risk": "<item>", '
    '"likelihood": "low|medium|high"}], "decision_rationale": "<2-3 '
    'sentences tying it together>"}'
)


# ---------------------------------------------------------------------------
# Evidence grading (rule-based, no LLM)
# ---------------------------------------------------------------------------

def _grade_evidence(side: str, claims: List[Dict[str, Any]],
                    data: Dict[str, Any]) -> Dict[str, Any]:
    """Check every claim's evidence citation against the actual data.

    A claim is 'grounded' if its evidence string names a section that
    exists in the data (optionally section.field). Uncited or bogus
    citations are flagged -- this is the FINSABER/debate-or-vote lesson
    applied: an ungrounded claim contributes nothing to the debate.
    """
    graded = []
    sections = set(data.keys())
    for c in claims or []:
        ev = (c.get("evidence") or "").strip()
        if not ev:
            graded.append({"claim": c.get("claim", ""),
                           "evidence": "", "grounded": False,
                           "reason": "no evidence citation"})
            continue
        sec, _, fld = ev.partition(".")
        ok = sec in sections
        if ok and fld:
            val = data.get(sec)
            # Field check: dict sections -> direct key; list sections
            # (e.g. earnings history) -> key inside any item.
            if isinstance(val, dict):
                ok = fld in val
            elif isinstance(val, list):
                ok = any(isinstance(i, dict) and fld in i for i in val)
        graded.append({"claim": c.get("claim", ""), "evidence": ev,
                       "grounded": ok,
                       "reason": "ok" if ok else
                       (f"section '{sec}' not present in gathered data"
                        if sec not in sections else
                        f"field '{fld}' not found in section '{sec}'")})
    grounded = sum(1 for g in graded if g["grounded"])
    return {
        "side": side,
        "n_claims": len(graded),
        "grounded": grounded,
        "ungrounded": len(graded) - grounded,
        "sections_cited": sorted({g["evidence"].split(".")[0]
                                  for g in graded if g["evidence"]}),
        "claims": graded,
    }


# ---------------------------------------------------------------------------
# Deterministic valuation (pure Python -- the LLM never writes numbers)
# ---------------------------------------------------------------------------

def _valuation(sym: str, data: Dict[str, Any],
               price: Optional[float]) -> Dict[str, Any]:
    """Compute an honest, deterministic valuation from the gathered data.

    Uses only what is in `data`: trailing P/E, ROE, debt/equity, last
    earnings surprises, and the next-quarter EPS consensus estimate.
    Every input is logged; missing inputs produce explicit N/A, never a
    guess. This is the AlphaAnalyst "the LLM is a writer, not a knower"
    discipline: these numbers are computed, not narrated.
    """
    out = {"sym": sym, "price": price, "deterministic": True,
           "inputs": {}, "outputs": {}, "notes": []}
    f = data.get("fundamentals") or {}
    out["inputs"]["pe_ttm"] = f.get("pe_ttm")
    out["inputs"]["roe_ttm"] = f.get("roe_ttm")
    out["inputs"]["debt_eq"] = f.get("debt_eq")
    out["inputs"]["ps_ttm"] = f.get("ps_ttm")

    # Forward EPS: next-quarter consensus estimate annualized (x4), if the
    # catalyst calendar gave us one.
    cat = data.get("catalyst") or {}
    fwd_eps = None
    if isinstance(cat, dict) and cat.get("eps_est"):
        fwd_eps = cat["eps_est"] * 4
        out["inputs"]["fwd_eps_annualized"] = round(fwd_eps, 2)
        out["notes"].append("fwd EPS = next-quarter consensus EPS x 4 "
                            "(annualized from a single quarter; crude)")

    # Trailing EPS and implied EPS growth from the earnings history.
    pe = f.get("pe_ttm")
    eps_growth = None
    if price and pe:
        trailing_eps = price / pe
        out["inputs"]["trailing_eps"] = round(trailing_eps, 2)
    earn = data.get("earnings")
    if isinstance(earn, list) and len(earn) >= 2:
        try:
            ys = [e["actual"] for e in earn if e.get("actual")]
            if len(ys) >= 2 and ys[0]:
                eps_growth = ys[0] / ys[-1] - 1.0
                out["inputs"]["eps_growth_trend"] = round(eps_growth, 3)
                out["notes"].append(
                    "EPS growth = latest actual EPS vs the oldest EPS in "
                    "the gathered history (rough trend)")
        except Exception:
            pass

    if eps_growth and eps_growth > 0 and pe:
        out["outputs"]["peg"] = round(pe / (eps_growth * 100), 2)
        out["notes"].append("PEG = trailing P/E / trailing EPS growth %")
    else:
        out["outputs"]["peg"] = None
        out["notes"].append("PEG unavailable (no positive EPS growth trend "
                            "in gathered history)")

    # Forward P/E the market is currently paying on the (crude) annualized
    # forward EPS -- a sanity anchor for the judge.
    if fwd_eps and price:
        out["outputs"]["fwd_pe"] = round(price / fwd_eps, 2)

    # Base / bull / bear fair-value targets from a sane P/E band.
    # Prefer forward EPS (consensus-implied); fall back to trailing EPS so
    # the judge still gets a mechanically-grounded anchor when the catalyst
    # calendar carries no consensus estimate.
    base_eps = fwd_eps or (price / pe if (price and pe) else None)
    if base_eps and pe:
        base_pe = pe
        bull_pe = round(pe * 1.25, 1)
        bear_pe = round(pe * 0.80, 1)
        out["inputs"]["pe_band"] = {"bear": bear_pe, "base": base_pe,
                                    "bull": bull_pe}
        out["notes"].append("P/E band = trailing P/E x 0.8 / 1.0 / 1.25; "
                            "mechanistic, no sector judgment")
        out["outputs"]["fair_value_basis"] = (
            "forward EPS (consensus annualized)" if fwd_eps
            else "trailing EPS")
        out["outputs"]["fair_value"] = {
            "bear": round(base_eps * bear_pe, 2),
            "base": round(base_eps * base_pe, 2),
            "bull": round(base_eps * bull_pe, 2),
        }
        if price:
            out["outputs"]["upside_base"] = round(
                base_eps * base_pe / price - 1.0, 3)
    else:
        out["outputs"]["fair_value"] = None
        out["notes"].append("No forward/trailing EPS or P/E available "
                            "-- fair value NOT computed (abstain, never "
                            "fabricate)")

    out["outputs"]["quality_signals"] = {
        "roe_ttm": f.get("roe_ttm"),
        "debt_eq": f.get("debt_eq"),
    }
    return out


# ---------------------------------------------------------------------------
# The debate
# ---------------------------------------------------------------------------

def _run_researcher(side: str, sym: str, data: Dict[str, Any],
                    errors: List[str], strong: bool = True) -> Optional[dict]:
    view = _data_view(sym, data, side)
    # .replace() not .format() -- the prompt contains literal JSON braces.
    return _llm_json(_RESEARCHER_SYSTEM.replace("{side}", side), view,
                     errors, label=f"{side}_researcher", strong=strong)


def _run_rebuttal(side: str, opposing: Optional[dict], sym: str,
                  data: Dict[str, Any], errors: List[str]) -> Optional[dict]:
    if not opposing or not opposing.get("claims"):
        return None
    opp_claims = json.dumps(opposing.get("claims", []), ensure_ascii=False)
    view = _data_view(sym, data, side)
    user = (f"OPPOSING ({'bear' if side == 'bull' else 'bull'}) CLAIMS:\n"
            f"{opp_claims}\n\nDATA (same as before):\n{view}")
    # .replace() not .format() -- the prompt contains literal JSON braces.
    return _llm_json(_REBUTTAL_SYSTEM.replace("{side}", side), user, errors,
                     label=f"{side}_rebuttal", strong=False)


def _run_judge(sym: str, data: Dict[str, Any], price: Optional[float],
               bull: Optional[dict], bear: Optional[dict],
               rebuttals: Dict[str, Any], grading: Dict[str, Any],
               val: Dict[str, Any], errors: List[str]) -> Optional[dict]:
    def _side_summary(side_result: Optional[dict], side: str) -> str:
        if not side_result:
            return f"{side}: (no output)"
        claims = "\n".join(
            f"- [{c.get('impact')}] {c.get('claim')} "
            f"(evidence: {c.get('evidence')})"
            for c in side_result.get("claims", []))
        return f"{side} (confidence {side_result.get('confidence')}):\n{claims}"

    rb = rebuttals.get("bull") or {}
    rbe = rebuttals.get("bear") or {}
    rebuttal_txt = (
        "Bull's answers to bear:\n" +
        ("\n".join(f"- {r.get('target_claim')} -> {r.get('response')}"
                   for r in rb.get("rebuttals", [])) or "(none)") +
        "\nBear's answers to bull:\n" +
        ("\n".join(f"- {r.get('target_claim')} -> {r.get('response')}"
                   for r in rbe.get("rebuttals", [])) or "(none)"))

    grading_txt = "\n".join(
        f"{g['side']}: {g['grounded']}/{g['n_claims']} claims grounded "
        f"(cited sections: {', '.join(g['sections_cited'])})"
        for g in grading.values() if isinstance(g, dict) and g.get("side"))

    user = (
        f"TICKER: {sym}\nPRICE: {price}\n\n"
        f"=== BULL CASE ===\n{_side_summary(bull, 'bull')}\n\n"
        f"=== BEAR CASE ===\n{_side_summary(bear, 'bear')}\n\n"
        f"=== REBUTTALS ===\n{rebuttal_txt}\n\n"
        f"=== EVIDENCE GRADING ===\n{grading_txt or '(no grading)'}\n\n"
        f"=== DETERMINISTIC VALUATION (computed in Python; do NOT alter) ===\n"
        f"{json.dumps(val, indent=1, default=str)}\n\n"
        f"Produce the final verdict JSON per your system rules."
    )
    return _llm_json(_JUDGE_SYSTEM, user, errors, label="judge", strong=True)


# ---------------------------------------------------------------------------
# Report writer (deterministic assembly -- no LLM numbers)
# ---------------------------------------------------------------------------

def _fmt_pct(x: Any) -> str:
    try:
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return "n/a"


def _render_markdown(res: ReportResult) -> str:
    sym = res.sym
    val = res.valuation or {}
    judge = res.judge or {}
    sc = judge.get("scenarios") or {}
    L = ["# %s — Equity Research Report (agent debate)" % sym, ""]
    L.append(f"*Generated {res.generated_utc} UTC | "
             f"data sections: {', '.join(res.data_sections) or 'none'}*")
    L.append("")
    L.append("> Research only. Not financial advice. All numbers computed "
             "deterministically from gathered data; LLM writes no numbers.")
    L.append("")

    # --- Expected-return headline (current price -> predicted 1-yr price) ---
    base_pt = (sc.get("base") or {}).get("pt")
    exp_ret = ((base_pt / res.price - 1.0) if (base_pt and res.price) else None)
    L.append("## 1. Expected return (current → predicted 1-yr price)")
    L.append("")
    L.append("| Current price | Predicted price (12-mo) | Expected return |")
    L.append("|---|---|---|")
    L.append(f"| {res.price or 'n/a'} | {base_pt or 'n/a'} | "
             f"**{_fmt_pct(exp_ret)}** |")
    L.append("")
    if exp_ret is None:
        L.append("> _No predicted 12-mo price is claimed: this name has no "
                 "forward-consensus EPS anchor in the free data, so the "
                 "valuation abstains (never fabricate). Expected return is "
                 "listed as n/a._")
        L.append("")
    elif base_pt == (res.price or 0):
        L.append("> _Predicted price = current price: the deterministic "
                 "trailing-EPS valuation is ambiguous on direction, so the "
                 "judge holds at spot. Treat as no edge signal._")
        L.append("")
    if sc:
        L.append("| Scenario | Prob | 12-mo PT | Thesis |")
        L.append("|---|---|---|---|")
        for k in ("bull", "base", "bear"):
            s = sc.get(k) or {}
            L.append(f"| {k} | {_fmt_pct(s.get('prob'))} | "
                     f"{s.get('pt', 'n/a')} | {(s.get('thesis') or '')[:100]} |")
        L.append("")

    # Rating & price targets
    L.append("## 2. Rating")
    L.append("")
    rating = judge.get("rating") or "n/a"
    conv = judge.get("conviction")
    L.append(f"| Rating | Conviction | Convergence |")
    L.append(f"|---|---|---|")
    L.append(f"| **{rating}** | {conv if conv is not None else 'n/a'} | "
             f"{'yes' if judge.get('convergence') else 'no'} |")
    L.append("")

    # Thesis
    if judge.get("decision_rationale"):
        L.append("## 3. Investment thesis")
        L.append("")
        L.append(judge["decision_rationale"])
        L.append("")

    # The debate
    L.append("## 4. The debate")
    L.append("")
    for side, sr in (("BULL", res.bull), ("BEAR", res.bear)):
        L.append(f"### {side} case")
        if not sr:
            L.append("_(no output)_")
            continue
        for c in sr.get("claims", []):
            L.append(f"- [{c.get('impact')}] {c.get('claim')} "
                     f"`{c.get('evidence')}`")
        L.append("")
    L.append("### Rebuttals")
    for side in ("bull", "bear"):
        rb = (res.rebuttals.get(side) or {}).get("rebuttals") or []
        L.append(f"**{side} answering the opposite side:**")
        if not rb:
            L.append("_(none)_")
        for r in rb:
            tag = "concede" if r.get("concede") else "rebut"
            L.append(f"- [{tag}] {r.get('target_claim')} → "
                     f"{r.get('response')} `{r.get('counter_evidence') or ''}`")
        L.append("")

    # Evidence grading
    L.append("## 5. Evidence grading (rule-based, against gathered data)")
    L.append("")
    for side in ("bull", "bear"):
        g = res.grading.get(side) or {}
        if not g:
            continue
        L.append(f"**{side}:** {g.get('grounded')}/{g.get('n_claims')} "
                 f"claims grounded | cited sections: "
                 f"{', '.join(g.get('sections_cited') or []) or 'none'}")
        for c in g.get("claims", []):
            mark = "✅" if c.get("grounded") else "⚠️"
            L.append(f"- {mark} {c.get('claim')} (`{c.get('evidence')}`) "
                     f"— {c.get('reason')}")
        L.append("")

    # Valuation
    L.append("## 6. Deterministic valuation (pure Python)")
    L.append("")
    L.append("| Input | Value |")
    L.append("|---|---|")
    for k, v in (val.get("inputs") or {}).items():
        L.append(f"| {k} | {v} |")
    L.append("")
    fv = (val.get("outputs") or {}).get("fair_value")
    if fv:
        up = (val.get("outputs") or {}).get("upside_base")
        L.append(f"| Fair value (bear/base/bull) | {fv['bear']} / "
                 f"{fv['base']} / {fv['bull']} |")
        L.append(f"| Implied upside to base | {_fmt_pct(up)} |")
    else:
        L.append("_Fair value not computed (insufficient data — abstain "
                 "rather than fabricate)._")
    L.append("")
    L.append("PEG: %s | quality: ROE %s, D/E %s" % (
        (val.get("outputs") or {}).get("peg") or "n/a",
        (val.get("outputs") or {}).get("quality_signals", {}).get("roe_ttm")
        or "n/a",
        (val.get("outputs") or {}).get("quality_signals", {}).get("debt_eq")
        or "n/a"))
    L.append("")
    for n in val.get("notes", []):
        L.append(f"- _note: {n}_")
    L.append("")

    # Catalysts & risks
    L.append("## 7. Catalysts & risks")
    L.append("")
    if judge.get("catalysts"):
        L.append("| Catalyst | Date | Impact |")
        L.append("|---|---|---|")
        for c in judge["catalysts"]:
            L.append(f"| {c.get('catalyst')} | {c.get('date')} | "
                     f"{c.get('impact')} |")
        L.append("")
    if judge.get("risks"):
        L.append("| Risk | Likelihood |")
        L.append("|---|---|")
        for r in judge["risks"]:
            L.append(f"| {r.get('risk')} | {r.get('likelihood')} |")
        L.append("")

    # Data appendix
    L.append("## 8. Data appendix")
    L.append("")
    for k in res.data_sections:
        L.append(f"- `{k}` — {_SECTION_LABELS.get(k, '')}")
    L.append("")
    L.append("## 9. Disclaimer")
    L.append("")
    L.append("Generated by the world-trader agent debate pipeline. "
             "Research only; not investment advice. Markets move fast — "
             "verify live prices and current filings before any decision.")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Top level
# ---------------------------------------------------------------------------

def generate_report(sym: str, force: bool = False,
                    out_dir: str = DEFAULT_OUT_DIR) -> ReportResult:
    """Run the full debate and write an equity research report for `sym`.

    Skips (returns an empty ReportResult with an error note) if a report
    for the same day already exists, unless force=True.
    """
    t0 = time.time()
    res = ReportResult(sym=sym.upper(),
                       generated_utc=datetime.utcnow().isoformat(timespec="seconds") + "Z")
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    md_path = os.path.join(out_dir, f"{res.sym}_{today}.md")
    js_path = os.path.join(out_dir, f"{res.sym}_{today}.json")
    if not force and os.path.exists(md_path):
        res.errors.append(f"report for {res.sym} already exists for {today} "
                          f"(use force=True to regenerate)")
        res.elapsed_sec = time.time() - t0
        return res

    # 1. data
    data = _gather(res.sym)
    res.data_sections = [k for k in _SECTION_LABELS if k in data]
    price = None
    q = data.get("quote") or {}
    price = q.get("c") or q.get("price")
    res.price = price

    # 2. bull & bear (anti-sycophancy ordering)
    res.bull = _run_researcher("bull", res.sym, data, res.errors)
    res.bear = _run_researcher("bear", res.sym, data, res.errors)

    # 3. rebuttal round
    res.rebuttals["bear"] = _run_rebuttal("bear", res.bull, res.sym, data,
                                          res.errors)
    res.rebuttals["bull"] = _run_rebuttal("bull", res.bear, res.sym, data,
                                          res.errors)

    # 4. evidence grading (rule-based)
    if res.bull:
        res.grading["bull"] = _grade_evidence("bull", res.bull.get("claims"),
                                              data)
    if res.bear:
        res.grading["bear"] = _grade_evidence("bear", res.bear.get("claims"),
                                              data)

    # 5. deterministic valuation
    res.valuation = _valuation(res.sym, data, price)

    # 6. judge
    res.judge = _run_judge(res.sym, data, price, res.bull, res.bear,
                           res.rebuttals, res.grading, res.valuation,
                           res.errors)

    # 7. write
    md = _render_markdown(res)
    with open(md_path, "w") as f:
        f.write(md)
    with open(js_path, "w") as f:
        json.dump(res.as_dict(), f, indent=2, default=str)
    res.report_path = md_path
    res.json_path = js_path
    res.elapsed_sec = round(time.time() - t0, 1)
    return res


def generate_watchlist(tickers: List[str], force: bool = False,
                       out_dir: str = DEFAULT_OUT_DIR) -> List[ReportResult]:
    """Generate reports for several tickers, sequentially (rate-safe)."""
    results = []
    for t in tickers:
        r = generate_report(t, force=force, out_dir=out_dir)
        results.append(r)
        status = "done" if r.report_path else ("skipped" if r.errors else "failed")
        print(f"[research-report] {t}: {status} "
              f"({r.elapsed_sec}s, errors={len(r.errors)})")
        if r.errors:
            for e in r.errors:
                print(f"    - {e}")
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="agent debate -> equity research report")
    ap.add_argument("sym", nargs="?", help="ticker to cover")
    ap.add_argument("--watchlist", default=None,
                    help="comma-separated tickers to cover in sequence")
    ap.add_argument("--force", action="store_true",
                    help="regenerate today's report if it exists")
    args = ap.parse_args()
    if args.watchlist:
        generate_watchlist([s.strip().upper() for s in
                            args.watchlist.split(",") if s.strip()])
    elif args.sym:
        r = generate_report(args.sym.upper(), force=args.force)
        print(json.dumps(r.as_dict(), indent=2, default=str))
        if r.report_path:
            print("\n---\nreport:", r.report_path)
    else:
        ap.print_help()
