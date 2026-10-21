"""Signal processor (CryptoTradingAgents-inspired).

CryptoTradingAgents has a `SignalProcessor` class
(tradingagents/graph/signal_processing.py) that takes the full final
trader output and distills it to a core BUY / SELL / HOLD decision with
a confidence score. We adopt the same idea:

  - Input: the trader dict (side, entry, stop, target, size_pct, ...)
    plus the risk_manager's approval/veto and the research_manager's plan.
  - Output: a compact "signal" dict with a single canonical action,
    confidence, and the key levels.

This is used in two places:
  1. As a final LLM-free post-processing step that gives us a clean
     signal for downstream consumers (CLI, JSON API, future auto-trader).
  2. As the input to the track-record scorer (so we score roles against
     a deterministic signal, not the raw trader dict).

The distillation is rule-based (no LLM) so it's deterministic and cheap.
The LLM-based trader still produces the rich ticket; we just normalize
it into a signal here.
"""
from __future__ import annotations
from typing import Any, Dict, Optional


def process_signal(trader: Optional[Dict[str, Any]],
                   risk_manager: Optional[Dict[str, Any]] = None,
                   research_manager: Optional[Dict[str, Any]] = None,
                   regime_label: str = "unknown") -> Dict[str, Any]:
    """Distill the agent run into a compact BUY/SELL/HOLD signal.

    Returns a dict with:
        action:     "BUY" | "SELL" | "HOLD"
        side:       "long" | "short" | None
        confidence: 0.0 - 1.0
        entry:      float | None
        stop:       float | None
        target:     float | None
        rr:         float | None
        size_pct:   float  (0 if HOLD)
        timeframe:  str
        sym:        str | None
        regime:     str
        skip_reason: str (only present when action == HOLD)
    """
    # Default: HOLD
    hold = {
        "action": "HOLD",
        "side": None,
        "confidence": 0.0,
        "entry": None,
        "stop": None,
        "target": None,
        "rr": None,
        "size_pct": 0.0,
        "timeframe": "intraday",
        "sym": None,
        "regime": regime_label,
        "skip_reason": "no_trade",
    }

    # Risk manager veto short-circuits everything.
    if risk_manager and isinstance(risk_manager, dict):
        if risk_manager.get("approved") is False:
            hold["skip_reason"] = f"risk_manager_veto: {risk_manager.get('reason','')[:120]}"
            return hold

    # Research manager can also say skip.
    if research_manager and isinstance(research_manager, dict):
        if (research_manager.get("action") == "skip"
                or not research_manager.get("action")):
            hold["skip_reason"] = f"research_manager_skip: {research_manager.get('rationale','')[:120]}"
            # If risk_manager also didn't approve, this is the reason.
            return hold

    if not trader or not isinstance(trader, dict):
        hold["skip_reason"] = "trader_no_output"
        return hold

    side = (trader.get("side") or trader.get("action") or "").lower()
    if side not in ("long", "short"):
        hold["skip_reason"] = f"trader_invalid_side: {side!r}"
        return hold

    # Required levels
    entry = trader.get("entry")
    stop = trader.get("stop")
    target = trader.get("target")
    rr = trader.get("rr")
    if not all(isinstance(x, (int, float)) for x in (entry, stop, target, rr)):
        hold["skip_reason"] = "trader_missing_levels"
        return hold

    # R:R floor: skip if below 1.5 (our house minimum is 2.0, but we
    # tolerate 1.5 here so the signal is still emitted -- the risk
    # manager should have caught anything < 2.0 already).
    if rr < 1.5:
        hold["skip_reason"] = f"rr_too_low: {rr:.2f}"
        return hold

    size_pct = trader.get("size_pct")
    if not isinstance(size_pct, (int, float)) or size_pct <= 0:
        hold["skip_reason"] = "size_pct_not_positive"
        return hold

    # Confidence: blend trader confidence with R:R and regime alignment.
    base_conf = trader.get("confidence")
    if not isinstance(base_conf, (int, float)):
        base_conf = 0.5
    # R:R bonus: R:R >= 3 adds up to +0.10, R:R < 2 subtracts up to -0.10
    if rr >= 3.0:
        rr_bonus = 0.10
    elif rr < 2.0:
        rr_bonus = -0.10
    else:
        rr_bonus = 0.0
    # Regime alignment: long in trending_bull or short in trending_bear
    # gets a small +0.05; opposing the regime gets -0.05.
    if (side == "long" and regime_label == "trending_bull") or \
       (side == "short" and regime_label == "trending_bear"):
        regime_bonus = 0.05
    elif (side == "long" and regime_label == "trending_bear") or \
         (side == "short" and regime_label == "trending_bull"):
        regime_bonus = -0.05
    else:
        regime_bonus = 0.0

    confidence = max(0.0, min(1.0, base_conf + rr_bonus + regime_bonus))

    return {
        "action": "BUY" if side == "long" else "SELL",
        "side": side,
        "confidence": round(confidence, 3),
        "entry": float(entry),
        "stop": float(stop),
        "target": float(target),
        "rr": float(rr),
        "size_pct": float(size_pct),
        "timeframe": trader.get("timeframe", "intraday"),
        "sym": trader.get("sym"),
        "regime": regime_label,
    }


def signal_line(signal: Dict[str, Any]) -> str:
    """One-line human-readable signal for CLI/log output."""
    if signal.get("action") == "HOLD":
        return f"HOLD  ({signal.get('skip_reason','no_trade')})"
    return (
        f"{signal['action']}  {signal.get('sym','?')}  "
        f"entry={signal.get('entry')}  stop={signal.get('stop')}  "
        f"target={signal.get('target')}  R:R={signal.get('rr')}  "
        f"size={signal.get('size_pct')}%  conf={signal.get('confidence')}  "
        f"[{signal.get('timeframe')}]  regime={signal.get('regime')}"
    )
