"""Multi-agent orchestrator.

The graph is a plain Python function sequence (no langgraph dependency):

  1. scan_markets tool  -> pick top candidate (or use the user-supplied sym)
  2. 5 analysts          -> market, fundamentals, news, sentiment, social
  3. 2 researchers       -> bull, bear (debate the analysts' reads)
  4. 3 risk debators     -> aggressive, conservative, neutral (judge the plan)
  5. research manager    -> synthesize debate into a plan
  6. risk manager        -> portfolio-level veto / sizing
  7. trader              -> concrete ticket (entry/stop/target/size/order)
  8. reflector           -> write lessons to long-term memory

Each step:
  - Calls wt.agent.llm_chat.chat() with the role-specific prompt.
  - Parses JSON response.
  - Stores the parsed dict in short-term memory.
  - Passes the relevant subset forward to the next node.

If any step fails (no LLM key, parse error, all tools failed), the
orchestrator degrades gracefully: it returns what it has with an "error"
field, never raises. This matches the project's "never let an LLM failure
kill the scan" convention.
"""
from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import memory, prompts
from .llm_chat import chat, parse_json_response, available_provider
from .tools_registry import (call_tool, render_tool_catalog,
                             render_tool_call_log, tool_call_log)
from . import regime_router, track_record, signal_processor


@dataclass
class AgentResult:
    """Final artifact from a single agent run."""
    candidate: Optional[Dict[str, Any]] = None
    analysts: Dict[str, Any] = field(default_factory=dict)
    bull: Optional[Dict[str, Any]] = None
    bear: Optional[Dict[str, Any]] = None
    risk_debate: Dict[str, Any] = field(default_factory=dict)
    research_manager: Optional[Dict[str, Any]] = None
    risk_manager: Optional[Dict[str, Any]] = None
    trader: Optional[Dict[str, Any]] = None
    reflector: Optional[Dict[str, Any]] = None
    # New fields (regime-aware routing + signal-processor)
    regime_label: Optional[str] = None
    signal: Optional[Dict[str, Any]] = None
    track_records: Optional[Dict[str, Any]] = None
    debate_skipped: bool = False
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    elapsed_sec: float = 0.0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "candidate": self.candidate,
            "analysts": self.analysts,
            "bull": self.bull,
            "bear": self.bear,
            "risk_debate": self.risk_debate,
            "research_manager": self.research_manager,
            "risk_manager": self.risk_manager,
            "trader": self.trader,
            "reflector": self.reflector,
            "regime_label": self.regime_label,
            "signal": self.signal,
            "track_records": self.track_records,
            "debate_skipped": self.debate_skipped,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "elapsed_sec": round(self.elapsed_sec, 2),
        }


def _safe_call_tool(name: str, **kwargs) -> Optional[Any]:
    """Wrap call_tool so a failed tool never kills the agent."""
    try:
        return call_tool(name, **kwargs)
    except Exception as e:
        return {"error": repr(e)[:300]}


def _render_analyst_outputs(analysts: Dict[str, Any]) -> str:
    """Compact string of all analyst outputs for the researcher prompts."""
    lines = []
    for role, out in analysts.items():
        if out is None:
            lines.append(f"{role}: (failed)")
        elif isinstance(out, dict) and "error" in out and len(out) == 1:
            lines.append(f"{role}: ERROR {out['error']}")
        else:
            lines.append(f"{role}: {json.dumps(out, default=str)[:600]}")
    return "\n".join(lines)


def _today() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _llm_call(system_prompt: str, user_prompt: str, errors: List[str],
              label: str, strong: bool = False) -> Optional[dict]:
    """Standard pattern: call LLM, parse JSON, log errors."""
    if available_provider() is None:
        errors.append(f"{label}: no LLM provider configured (need XAI_API_KEY "
                      "or ANTHROPIC_API_KEY)")
        return None
    raw = chat(system_prompt, user_prompt, strong=strong,
               temperature=0.2, max_tokens=1800)
    if not raw:
        errors.append(f"{label}: LLM returned empty")
        return None
    parsed = parse_json_response(raw)
    if parsed is None:
        errors.append(f"{label}: failed to parse JSON from LLM "
                      f"(first 200 chars: {raw[:200]!r})")
        return None
    return parsed


def _pick_top_candidate(scan_rows: List[Dict[str, Any]],
                        sym: Optional[str]) -> Optional[Dict[str, Any]]:
    """If the user gave a sym, find it in the scan; else take the top row."""
    if not scan_rows:
        return None
    if sym:
        sym_l = sym.lower()
        for r in scan_rows:
            if str(r.get("sym", "")).lower() == sym_l:
                return r
        # Not in scan; return a stub so deep_dive can still run
        return {"sym": sym, "region": "US", "price": None,
                "thesis": "(user-specified; not in current scan)"}
    return scan_rows[0]


def run_agent(sym: Optional[str] = None,
              include_arbs: bool = True,
              max_candidates: int = 1,
              scan_only: bool = False) -> AgentResult:
    """Run the full multi-agent pipeline.

    Args:
        sym: if given, focus the agent on this ticker. If None, the agent
            picks the top-ranked candidate from the scan.
        include_arbs: if True, also probe all arb modules for non-directional
            ideas and include them in the final artifact.
        max_candidates: number of candidates to run the full debate on (1 by
            default; >1 is much slower and not recommended yet).
        scan_only: if True, skip all LLM calls and return only the scan
            results (plus arbs). Useful when no LLM provider is available,
            or for a fast "what does the scanner see right now" check.

    Returns:
        AgentResult with every step's output (or None where it failed).
    """
    t0 = time.time()
    res = AgentResult()
    portfolio = memory.read_portfolio()
    lessons = memory.recent_lessons(limit=10)
    # Load per-role track records (HydraQuant-style meta-synthesis input).
    track_rates = track_record.hit_rates()
    res.track_records = track_rates

    # ----- Step 1: scan_markets -------------------------------------------
    scan = _safe_call_tool("scan_markets", top_n=15, live_only=True)
    if scan is None or (isinstance(scan, dict) and scan.get("error")):
        res.errors.append("scan_markets failed")
        scan_rows = []
        regime = "unknown"
        fg = None
        macro = {}
    else:
        scan_rows = scan.get("rows", []) if isinstance(scan, dict) else []
        regime = scan.get("regime", "unknown") if isinstance(scan, dict) else "unknown"
        fg = scan.get("fear_greed") if isinstance(scan, dict) else None
        macro = scan.get("macro", {}) if isinstance(scan, dict) else {}

    # Classify the regime into one of 6 labels and stash on the result.
    # (HydraQuant-inspired: regime drives agent selection + weight profile.)
    res.regime_label = regime_router.classify_regime(regime, fg)

    # ----- Step 2: pick candidate -----------------------------------------
    candidate = _pick_top_candidate(scan_rows, sym)
    res.candidate = candidate

    if candidate is None:
        res.errors.append("no candidate identified (scan returned no rows "
                          "and no sym was provided)")
        if include_arbs:
            arbs = _safe_call_tool("list_arb_setups")
            res.analysts["arbs"] = arbs
        res.tool_calls = tool_call_log()
        res.elapsed_sec = time.time() - t0
        return res

    cand_sym = candidate.get("sym", "")
    cand_region = candidate.get("region", "")

    # ----- scan_only early exit -------------------------------------------
    # If scan_only (or no LLM provider), return the scan results + arbs
    # without running the debate. This keeps the agent useful even when
    # every LLM provider is down.
    if scan_only or available_provider() is None:
        if available_provider() is None and not scan_only:
            res.errors.append("no LLM provider available -- returning scan-only")
        if include_arbs:
            arbs = _safe_call_tool("list_arb_setups")
            if arbs and not (isinstance(arbs, dict) and arbs.get("error")):
                res.analysts["arbs"] = arbs
        # Add a few more useful context tools for the scan-only report
        sess = _safe_call_tool("market_sessions")
        if sess and not (isinstance(sess, dict) and sess.get("error")):
            res.analysts["market_sessions"] = sess
        res.tool_calls = tool_call_log()
        res.elapsed_sec = time.time() - t0
        return res

    # Context string for analysts: candidate + regime + macro + lessons
    ctx = json.dumps({
        "candidate": candidate,
        "regime": regime,
        "fear_greed": fg,
        "macro": macro,
        "prior_lessons": lessons,
        "portfolio": portfolio,
        "tools_available": render_tool_catalog(),
    }, default=str, indent=2)

    # ----- Step 3: analysts (regime-aware selection) ----------------------
    # HydraQuant-inspired: pick which analysts to run based on regime.
    # Always run market + fundamentals; the rest are regime-conditional.
    # In transitional / high-vol regimes, also run the macro-regime analyst
    # (opentrade/src/skills/macro-regime.md inspired).
    selected = regime_router.select_analysts(res.regime_label)
    all_templates = {
        "market": prompts.ANALYST_MARKET,
        "fundamentals": prompts.ANALYST_FUNDAMENTALS,
        "news": prompts.ANALYST_NEWS,
        "sentiment": prompts.ANALYST_SENTIMENT,
        "social": prompts.ANALYST_SOCIAL,
        "macro_regime": prompts.ANALYST_MACRO_REGIME,
    }
    for role in selected:
        tmpl = all_templates.get(role)
        if tmpl is None:
            continue
        user = tmpl.format(today=_today(), context=ctx, sym=cand_sym)
        out = _llm_call(prompts.PREAMBLE.format(today=_today()),
                        user, strong=False, errors=res.errors,
                        label=f"analyst/{role}")
        res.analysts[role] = out

    # Macro-regime analyst is mandatory in transitional or high-vol regimes
    # (it's the top-down check that overrides bottom-up bullishness).
    if (res.regime_label in ("transitional", "high_volatility")
            and "macro_regime" not in res.analysts):
        user = prompts.ANALYST_MACRO_REGIME.format(
            today=_today(), context=ctx, sym=cand_sym)
        out = _llm_call(prompts.PREAMBLE.format(today=_today()),
                        user, strong=False, errors=res.errors,
                        label="analyst/macro_regime")
        res.analysts["macro_regime"] = out

    # ----- Step 4: deep_dive for more fundamentals context ----------------
    # (Tool call -- not an LLM step. Adds to the context the researchers see.)
    dd = _safe_call_tool("deep_dive", sym=cand_sym, region=cand_region)
    if dd is not None:
        res.analysts["deep_dive"] = dd

    # ----- Step 5: bull & bear researchers --------------------------------
    analyst_outputs_str = _render_analyst_outputs(res.analysts)

    bull_user = prompts.RESEARCHER_BULL.format(
        today=_today(), sym=cand_sym, analyst_outputs=analyst_outputs_str)
    res.bull = _llm_call(prompts.PREAMBLE.format(today=_today()),
                         bull_user, strong=True, errors=res.errors,
                         label="researcher/bull")

    bear_user = prompts.RESEARCHER_BEAR.format(
        today=_today(), sym=cand_sym, analyst_outputs=analyst_outputs_str)
    res.bear = _llm_call(prompts.PREAMBLE.format(today=_today()),
                         bear_user, strong=True, errors=res.errors,
                         label="researcher/bear")

    # ----- Step 6: 3-way risk debate (with consensus-skip) ----------------
    # HydraQuant-inspired cost-skip: if bull & bear both arrive at high
    # confidence AND agree on direction, skip the 3-way debate and go
    # straight to the research manager. Saves 3 LLM calls on clear-cut
    # setups.
    bull_str = json.dumps(res.bull, default=str) if res.bull else "(bull failed)"
    bear_str = json.dumps(res.bear, default=str) if res.bear else "(bear failed)"

    if regime_router.consensus_skip(res.bull, res.bear):
        res.debate_skipped = True
        res.risk_debate = {
            "skipped": True,
            "reason": "bull/bear high-confidence consensus; debate skipped "
                      "to save LLM cost (HydraQuant-style Round 2 skip)",
        }
    else:
        res.debate_skipped = False
        agg_user = prompts.RISK_DEBATE_AGGRESSIVE.format(
            today=_today(), bull=bull_str, bear=bear_str)
        res.risk_debate["aggressive"] = _llm_call(
            prompts.PREAMBLE.format(today=_today()),
            agg_user, strong=True, errors=res.errors, label="debate/aggressive")

        agg_str = json.dumps(res.risk_debate.get("aggressive"), default=str)
        cons_user = prompts.RISK_DEBATE_CONSERVATIVE.format(
            today=_today(), bull=bull_str, bear=bear_str, aggressive=agg_str)
        res.risk_debate["conservative"] = _llm_call(
            prompts.PREAMBLE.format(today=_today()),
            cons_user, strong=True, errors=res.errors, label="debate/conservative")

        cons_str = json.dumps(res.risk_debate.get("conservative"), default=str)
        neut_user = prompts.RISK_DEBATE_NEUTRAL.format(
            today=_today(), bull=bull_str, bear=bear_str,
            aggressive=agg_str, conservative=cons_str)
        res.risk_debate["neutral"] = _llm_call(
            prompts.PREAMBLE.format(today=_today()),
            neut_user, strong=True, errors=res.errors, label="debate/neutral")

    # ----- Step 7: research manager ---------------------------------------
    risk_debate_str = json.dumps(res.risk_debate, default=str, indent=2)
    rm_user = prompts.RESEARCH_MANAGER_V2.format(
        today=_today(), bull=bull_str, bear=bear_str,
        risk_debate=risk_debate_str,
        regime_label=res.regime_label,
        regime_summary=regime_router.regime_summary(res.regime_label),
        weight_profile=json.dumps(
            regime_router.weight_profile(res.regime_label), default=str),
        track_records=track_record.format_track_records_for_prompt(track_rates),
    )
    res.research_manager = _llm_call(
        prompts.PREAMBLE.format(today=_today()),
        rm_user, strong=True, errors=res.errors, label="research_manager")

    # ----- Step 8: risk manager (portfolio veto) --------------------------
    if res.research_manager:
        plan_str = json.dumps(res.research_manager, default=str, indent=2)
        port_ctx_str = json.dumps(portfolio, default=str, indent=2)
        rmp_user = prompts.RISK_MANAGER.format(
            today=_today(), plan=plan_str, portfolio_context=port_ctx_str)
        res.risk_manager = _llm_call(
            prompts.PREAMBLE.format(today=_today()),
            rmp_user, strong=True, errors=res.errors, label="risk_manager")

    # ----- Step 9: trader (final ticket) ----------------------------------
    if res.risk_manager and res.risk_manager.get("approved"):
        plan_str = json.dumps(res.research_manager, default=str, indent=2)
        rmg_str = json.dumps(res.risk_manager, default=str, indent=2)
        tr_user = prompts.TRADER.format(
            today=_today(), plan=plan_str, risk_mgr=rmg_str)
        res.trader = _llm_call(
            prompts.PREAMBLE.format(today=_today()),
            tr_user, strong=True, errors=res.errors, label="trader")
    elif res.risk_manager and not res.risk_manager.get("approved"):
        res.errors.append(f"trade vetoed by risk manager: "
                          f"{res.risk_manager.get('veto_reason', '')}")
    else:
        res.errors.append("trader skipped: risk manager did not approve or failed")

    # ----- Step 9.5: signal processor (CryptoTradingAgents-inspired) -----
    # Distill the trader/risk_manager/research_manager output into a
    # compact BUY/SELL/HOLD signal with normalized confidence. Rule-based
    # (no LLM call) so it's deterministic and cheap.
    res.signal = signal_processor.process_signal(
        trader=res.trader,
        risk_manager=res.risk_manager,
        research_manager=res.research_manager,
        regime_label=res.regime_label or "unknown",
    )

    # ----- Step 10: reflector (memory) ------------------------------------
    decision_summary = json.dumps({
        "candidate": candidate,
        "research_manager": res.research_manager,
        "risk_manager": res.risk_manager,
        "trader": res.trader,
    }, default=str, indent=2)
    refl_user = prompts.REFLECTOR.format(
        today=_today(),
        decision_summary=decision_summary,
        tool_calls=render_tool_call_log())
    res.reflector = _llm_call(
        prompts.PREAMBLE.format(today=_today()),
        refl_user, strong=True, errors=res.errors, label="reflector")
    if res.reflector:
        try:
            memory.append_long_term({
                "sym": cand_sym,
                "reflector": res.reflector,
                "research_manager_action": (res.research_manager or {}).get("action"),
                "trader_sym": (res.trader or {}).get("sym"),
                "trader_side": (res.trader or {}).get("side"),
                "regime_label": res.regime_label,
                "signal": res.signal,
                "debate_skipped": res.debate_skipped,
            })
        except Exception as e:
            res.errors.append(f"memory write failed: {repr(e)[:200]}")

        # Write per-role track records (HydraQuant-style track-record
        # weighting). Use the reflector's role_scores if it produced them;
        # otherwise fall back to the deterministic heuristic scorer.
        try:
            role_scores = {}
            if isinstance(res.reflector, dict):
                rs = res.reflector.get("role_scores")
                if isinstance(rs, dict):
                    for k, v in rs.items():
                        if v in (-1, 0, 1):
                            role_scores[k] = int(v)
            if not role_scores:
                # Heuristic fallback: score each role against the final signal.
                final = {
                    "side": (res.signal or {}).get("side"),
                    "action": (res.signal or {}).get("action"),
                    "approved": bool(res.risk_manager and res.risk_manager.get("approved")),
                    "rr": (res.signal or {}).get("rr"),
                }
                for role in ("bull", "bear", "conservative",
                             "research_manager", "risk_manager"):
                    output = None
                    if role == "bull":
                        output = res.bull
                    elif role == "bear":
                        output = res.bear
                    elif role == "conservative":
                        output = res.risk_debate.get("conservative") if isinstance(res.risk_debate, dict) else None
                    elif role == "research_manager":
                        output = res.research_manager
                    elif role == "risk_manager":
                        output = res.risk_manager
                    s = track_record.score_role(role, output, final)
                    if s != 0:
                        role_scores[role] = s
            if role_scores:
                track_record.record_run(role_scores, ts=_today())
        except Exception as e:
            res.errors.append(f"track record write failed: {repr(e)[:200]}")

    # ----- Optional: arbs --------------------------------------------------
    if include_arbs:
        arbs = _safe_call_tool("list_arb_setups")
        if arbs:
            res.analysts["arbs"] = arbs

    res.tool_calls = tool_call_log()
    res.elapsed_sec = time.time() - t0
    return res


def render_result_text(res: AgentResult) -> str:
    """Human-readable summary of the agent run. Used by the CLI."""
    lines = []
    lines.append("=" * 72)
    # Detect scan-only mode: no LLM steps ran
    is_scan_only = (res.bull is None and res.bear is None
                    and res.research_manager is None
                    and res.candidate is not None)
    header = ("world-trader AI AGENT -- multi-agent debate result"
              if not is_scan_only else
              "world-trader AI AGENT -- scan-only snapshot")
    lines.append(header)
    lines.append("=" * 72)
    if res.regime_label:
        lines.append(f"Regime: {res.regime_label} -- "
                     f"{regime_router.regime_summary(res.regime_label)}")
    if res.debate_skipped:
        lines.append("Risk debate: SKIPPED (bull/bear consensus, HydraQuant-style cost-skip)")
    if res.signal:
        lines.append(f"Signal: {signal_processor.signal_line(res.signal)}")
    if res.track_records:
        lines.append("Track records (recent hit rates):")
        for role, r in res.track_records.items():
            lines.append(f"  - {role}: hit_rate={r['hit_rate']:.2f} (n={int(r['n'])})")
    if res.candidate:
        lines.append(f"\nCandidate: {res.candidate.get('sym','?')} "
                     f"({res.candidate.get('region','?')})  "
                     f"price={res.candidate.get('price')}")
        th = res.candidate.get('thesis')
        if th:
            lines.append(f"  thesis: {th}")
    if res.research_manager:
        rm = res.research_manager
        lines.append(f"\nResearch Manager: action={rm.get('action','?')}  "
                     f"R:R={rm.get('rr','?')}  size={rm.get('size_pct','?')}%  "
                     f"timeframe={rm.get('timeframe','?')}")
        if rm.get('rationale'):
            lines.append(f"  rationale: {rm['rationale']}")
        if rm.get('entry_zone'):
            lines.append(f"  entry zone: {rm['entry_zone']}  stop: {rm.get('stop')}  "
                         f"target: {rm.get('target')}")
    if res.risk_manager:
        rkm = res.risk_manager
        lines.append(f"\nRisk Manager: approved={rkm.get('approved')}  "
                     f"final_size={rkm.get('final_size_pct','?')}%")
        if rkm.get('veto_reason'):
            lines.append(f"  veto: {rkm['veto_reason']}")
    if res.trader:
        t = res.trader
        lines.append(f"\nTrader TICKET:")
        lines.append(f"  {t.get('side','?').upper()} {t.get('sym','?')}  "
                     f"order={t.get('order_type','?')}  qty={t.get('quantity_hint','?')}")
        lines.append(f"  stop={t.get('stop_price')}  target={t.get('target_price')}  "
                     f"R:R={t.get('rr')}")
        if t.get('options_structure'):
            lines.append(f"  options: {t['options_structure']}")
        if t.get('notes'):
            lines.append(f"  notes: {t['notes']}")
    # Bull/bear summary
    if res.bull:
        lines.append(f"\nBull: {res.bull.get('thesis','')}")
    if res.bear:
        lines.append(f"Bear: {res.bear.get('thesis','')}")
    # Scan-only extras: show the scan rows + arbs that the analysts would see
    if is_scan_only:
        arbs = res.analysts.get("arbs") if isinstance(res.analysts, dict) else None
        if arbs and isinstance(arbs, dict) and arbs.get("arbs"):
            lines.append("\nArbitrage setups (non-directional):")
            for kind, items in arbs["arbs"].items():
                if isinstance(items, list) and items:
                    lines.append(f"  {kind}: {len(items)} setups found")
                    for it in items[:3]:
                        if isinstance(it, dict):
                            lines.append(f"    - {it.get('sym') or it.get('pair') or it.get('label','?')}: "
                                         f"{json.dumps({k:v for k,v in it.items() if k not in ('sym','pair','label')}, default=str)[:160]}")
                elif isinstance(items, dict) and items.get("error"):
                    lines.append(f"  {kind}: ERR {items['error']}")
        sess = res.analysts.get("market_sessions") if isinstance(res.analysts, dict) else None
        if sess and isinstance(sess, dict) and sess.get("sessions"):
            lines.append(f"\nMarket sessions: {sess['sessions']}")
    # Errors
    if res.errors:
        lines.append("\nErrors:")
        for e in res.errors:
            lines.append(f"  - {e}")
    # Tool calls
    lines.append(f"\nTool calls ({len(res.tool_calls)}):")
    for c in res.tool_calls:
        status = "ok" if not c.get("error") else f"ERR {c['error']}"
        lines.append(f"  - {c['tool']} [{c['ms']}ms] {status}")
    lines.append(f"\nElapsed: {res.elapsed_sec:.1f}s")
    return "\n".join(lines)
