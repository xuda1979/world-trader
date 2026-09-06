"""CAMP_SHORT: honest shortability model (IBKR reality), TDD-tested.
Tiers (defaults calibrated to published IBKR/professional borrow schedules):
  EASY   ~0.5%/yr  (general collateral, large caps)
  MEDIUM ~2.0%/yr  (moderate HTB)
  HARD   ~8.0%/yr  (small/micro-cap HTB, thin locate supply)
  NONE   un-shortable -> short leg MUST be dropped (fail-closed), not costed.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

ANN = 252.0
TIERS = {"EASY": 0.005, "MEDIUM": 0.02, "HARD": 0.08, "NONE": None}


def shortability_gate(weights: pd.DataFrame, tier_by_name: dict,
                      default_tier: str = "EASY"):
    """Apply borrow reality to a weights frame.

    - names with tier NONE: short weights set to 0 (leg dropped), longs untouched.
    - surviving shorts accrue tiered borrow cost daily on short notional.
    Returns (weights_gated, borrow_cost_series, dropped_names). Fail-closed: an unknown
    tier raises; missing names get default_tier."""
    if default_tier not in TIERS:
        raise ValueError(f"unknown default_tier {default_tier}")
    tiers = {}
    for c in weights.columns:
        t = tier_by_name.get(c, default_tier)
        if t not in TIERS:
            raise ValueError(f"unknown tier {t} for {c}")
        tiers[c] = t
    w = weights.copy()
    dropped = [c for c, t in tiers.items() if t == "NONE"]
    for c in dropped:
        w[c] = w[c].clip(lower=0.0)   # drop the short leg only
    borrow = pd.Series(0.0, index=weights.index)
    for c, t in tiers.items():
        if t == "NONE":
            continue
        shorts = (-w[c].clip(upper=0.0))
        borrow = borrow + shorts * TIERS[t] / ANN
    return w, borrow, dropped


def mcap_tier(mcap_rank_frac: float) -> str:
    """Map a name's market-cap universe rank fraction (0=smallest) to a borrow tier.
    Calibration (research note, IBKR general): bottom ~10% micro-caps -> mostly HARD
    with a 20% slice un-shortable (caller models that separately by name);
    10-40% small -> MEDIUM; >40% -> EASY."""
    if mcap_rank_frac < 0.10:
        return "HARD"
    if mcap_rank_frac < 0.40:
        return "MEDIUM"
    return "EASY"
