"""Regime-aware agent selection (HydraQuant-inspired).

HydraQuant (ymcbzrgn/HydraQuant) selects 4-7 agents per debate from a pool
of 12 specialized agents, based on the current market regime. We adopt the
same idea but adapt it to our fixed-role pipeline:

  - Classify the regime into one of: trending_bull | trending_bear |
    ranging | high_volatility | transitional | unknown
  - Decide which ANALYSTS to run (we always run market + fundamentals, but
    sentiment/social/news are regime-conditional)
  - Decide whether the 3-way risk debate can be SKIPPED (consensus skip)
  - Pick the "weight profile" the research manager uses to weight bull vs
    bear vs risk-debate (e.g., in trending_bull, bull gets a slight boost;
    in high_volatility, risk-debate's conservative voice gets a boost)

The classifier is deterministic (rule-based) so it is cheap and
reproducible. The inputs are the regime dict and fear/greed already
collected by `scan_markets`.

Reference: HydraQuant README "Multi-Agent Debate" section -- 12 agents
(TrendFollower, MeanReverter, MomentumRider, FundingContrarian,
RiskMinimizer, DevilsAdvocate, EvidenceValidator, MacroCorrelator,
TemporalAnalyst, ExploiterAgent, DefenderAgent, ReflectionAgent), with
4-7 selected per debate based on regime.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Regime labels used throughout the agent layer.
REGIME_TRENDING_BULL = "trending_bull"
REGIME_TRENDING_BEAR = "trending_bear"
REGIME_RANGING = "ranging"
REGIME_HIGH_VOL = "high_volatility"
REGIME_TRANSITIONAL = "transitional"
REGIME_UNKNOWN = "unknown"

VALID_REGIMES = {
    REGIME_TRENDING_BULL, REGIME_TRENDING_BEAR, REGIME_RANGING,
    REGIME_HIGH_VOL, REGIME_TRANSITIONAL, REGIME_UNKNOWN,
}


def classify_regime(regime: Any, fear_greed: Any,
                    vix: Optional[float] = None) -> str:
    """Map the raw regime/fear-greed/VIX into one of our 6 regime labels.

    The `regime` coming from `wt.report.gather_regime` is typically a string
    like "Risk-On" / "Risk-Off" / "Neutral" or a dict with similar fields.
    We collapse it into a 6-way label that drives agent selection.

    Deterministic and LLM-free so it's cheap to call every run.
    """
    if isinstance(regime, dict):
        label = (regime.get("label") or regime.get("regime")
                 or regime.get("name") or "").lower()
    else:
        label = str(regime or "").lower()

    # VIX-based high-vol override (VIX > 28 = high-vol regime)
    if vix is not None and isinstance(vix, (int, float)) and vix >= 28.0:
        return REGIME_HIGH_VOL

    # Fear & Greed pull
    fg_val = None
    if isinstance(fear_greed, dict):
        for k in ("value", "score", "fg"):
            v = fear_greed.get(k)
            if isinstance(v, (int, float)):
                fg_val = v
                break
    elif isinstance(fear_greed, (int, float)):
        fg_val = fear_greed

    if "risk-on" in label or "risk_on" in label or "bull" in label:
        if fg_val is not None and fg_val >= 75:
            # Extreme greed on a risk-on tape = late-stage bull, mark
            # transitional so the agent doesn't blindly chase.
            return REGIME_TRANSITIONAL
        return REGIME_TRENDING_BULL
    if "risk-off" in label or "risk_off" in label or "bear" in label:
        return REGIME_TRENDING_BEAR
    if "neutral" in label or "range" in label:
        return REGIME_RANGING
    if "transitional" in label or "transition" in label:
        return REGIME_TRANSITIONAL

    # Fallback: infer from fear/greed if we have it
    if fg_val is not None:
        if fg_val >= 60:
            return REGIME_TRENDING_BULL
        if fg_val <= 25:
            return REGIME_TRENDING_BEAR
        if fg_val <= 45:
            return REGIME_RANGING
        return REGIME_TRANSITIONAL

    return REGIME_UNKNOWN


# Which analysts to run in each regime.
# Always run market + fundamentals (cheap, essential). The other three
# (news, sentiment, social) are regime-conditional -- this is the
# HydraQuant "select agents per regime" idea applied to our pipeline.
_DEFAULT_ANALYSTS = ("market", "fundamentals")
_REGIME_ANALYSTS: Dict[str, tuple] = {
    REGIME_TRENDING_BULL: ("market", "fundamentals", "news", "sentiment"),
    REGIME_TRENDING_BEAR: ("market", "fundamentals", "news", "sentiment"),
    REGIME_RANGING: ("market", "fundamentals", "sentiment"),
    REGIME_HIGH_VOL: ("market", "fundamentals", "news", "sentiment", "social"),
    REGIME_TRANSITIONAL: ("market", "fundamentals", "news", "sentiment", "social"),
    REGIME_UNKNOWN: ("market", "fundamentals", "news", "sentiment", "social"),
}


def select_analysts(regime_label: str) -> List[str]:
    """Return the ordered list of analyst roles to run for this regime."""
    return list(_REGIME_ANALYSTS.get(regime_label, _DEFAULT_ANALYSTS))


# Weight profile the research manager uses to weight the three voices.
# These are hints passed in the prompt, not hard weights (the LLM remains
# the judge). HydraQuant does something similar with agent track-record
# weighting in the meta-synthesis round.
_WEIGHT_PROFILES: Dict[str, Dict[str, float]] = {
    REGIME_TRENDING_BULL: {"bull": 1.10, "bear": 0.90, "conservative": 0.95},
    REGIME_TRENDING_BEAR: {"bull": 0.90, "bear": 1.10, "conservative": 1.10},
    REGIME_RANGING:       {"bull": 0.95, "bear": 0.95, "conservative": 1.05},
    REGIME_HIGH_VOL:      {"bull": 0.85, "bear": 0.95, "conservative": 1.20},
    REGIME_TRANSITIONAL:  {"bull": 0.95, "bear": 0.95, "conservative": 1.10},
    REGIME_UNKNOWN:       {"bull": 1.00, "bear": 1.00, "conservative": 1.05},
}


def weight_profile(regime_label: str) -> Dict[str, float]:
    """Return the bull/bear/conservative weight hints for the research mgr."""
    return dict(_WEIGHT_PROFILES.get(regime_label, _WEIGHT_PROFILES[REGIME_UNKNOWN]))


def consensus_skip(bull: Optional[Dict[str, Any]],
                   bear: Optional[Dict[str, Any]],
                   threshold: float = 0.75) -> bool:
    """Decide whether to SKIP the 3-way risk debate (HydraQuant cost-skip).

    HydraQuant skips Round 2 (cross-examination) when Round 1 consensus is
    already high. We apply the same idea to the risk debate: if BOTH bull
    and bear researchers independently arrive at high confidence (>threshold)
    AND they agree on direction (both not-short, or both not-long), we skip
    the aggressive/conservative/neutral debate and go straight to the
    research manager. This saves 3 LLM calls on clear-cut setups.

    Returns True if the debate should be skipped.
    """
    if not bull or not bear:
        return False
    b_conf = bull.get("confidence")
    r_conf = bear.get("confidence")
    if not isinstance(b_conf, (int, float)) or not isinstance(r_conf, (int, float)):
        return False
    if b_conf < threshold or r_conf < threshold:
        return False
    # Agree on direction: bull doesn't want to short AND bear doesn't want
    # to long means they both see long-bias (or no-trade). If bull would
    # short and bear would short, both see short-bias. Either is consensus.
    b_short = bool(bull.get("would_short"))
    r_short = bool(bear.get("would_short"))
    if b_short == r_short:
        return True
    # Also skip if both have low would_short AND confidence very high --
    # both see a clear long setup.
    if not b_short and not r_short and b_conf >= 0.85 and r_conf >= 0.85:
        return True
    return False


def regime_summary(regime_label: str) -> str:
    """One-line human-readable summary of the regime (for prompts/logs)."""
    return {
        REGIME_TRENDING_BULL: "Risk-on, bullish trend (favor longs, mind late-stage greed)",
        REGIME_TRENDING_BEAR: "Risk-off, bearish trend (favor shorts / cash, defensive)",
        REGIME_RANGING:       "Range-bound, no clear trend (mean-reversion favored)",
        REGIME_HIGH_VOL:      "High volatility / VIX elevated (size down, wider stops)",
        REGIME_TRANSITIONAL:  "Transitional tape (be cautious, smaller positions)",
        REGIME_UNKNOWN:       "Regime unclear (default to conservative sizing)",
    }.get(regime_label, "Regime unclear (default to conservative sizing)")
