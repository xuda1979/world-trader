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


def shortability_pregate(weights: pd.DataFrame, tier_by_name: dict,
                         default_tier: str = "EASY", preserve_gross: bool = True):
    """ROUND-2 hunt-template PRE-GATE (call BEFORE gates, after T+1 weights are built).

    Pipeline order: signal -> T+1 weights -> THIS -> costs -> gates. Fail-closed:
    unknown tier raises (book is never silently assumed shortable).

    - tier NONE: short leg dropped (fail-closed, never costed).
    - surviving shorts borrow at their tier rate, same-day on live weight.
    - preserve_gross=True: after dropping a leg, surviving legs are re-levered so book
      gross is unchanged (the sleeve keeps its vol-target; the dropped short's risk
      budget is redistributed, not lost).
    Returns (weights_gated, borrow_cost_series, info_dict) where info has dropped /
    gross_before / gross_after / borrow_ann_frac."""
    w, borrow0, dropped = shortability_gate(weights, tier_by_name, default_tier)
    info = dict(dropped=dropped, gross_before=None, gross_after=None,
                borrow_ann_frac=float(borrow0.mean() * ANN))
    if not dropped or not preserve_gross:
        return w, borrow0, info
    gb = weights.abs().sum(axis=1)
    ga = w.abs().sum(axis=1)
    scale = (gb / ga.replace(0.0, np.nan)).fillna(1.0)
    w = w.mul(scale, axis=0)
    borrow = pd.Series(0.0, index=weights.index)
    for c in weights.columns:
        t = tier_by_name.get(c, default_tier)
        if t == "NONE":
            continue
        borrow = borrow + (-w[c].clip(upper=0.0)) * TIERS[t] / ANN
    info.update(gross_before=float(gb.mean()), gross_after=float(ga.mul(scale, axis=0).mean()),
                borrow_ann_frac=float(borrow.mean() * ANN))
    return w, borrow, info


def tier_delta_cost(short_notional: pd.Series, base_rate: float, tier_rate: float) -> pd.Series:
    """Daily NAV drag (fraction/day) of moving `short_notional` from the base rate already
    charged inside a pre-netted sleeve to a tiered rate. Delta, not total: negative when the
    tier is cheaper than base (a credit — never clipped). Fail-closed on NaN or negative
    notional (a negative short notional is a construction bug, not zero)."""
    sn = pd.Series(short_notional, dtype=float)
    if sn.isna().any():
        raise ValueError("tier_delta_cost: NaN in short_notional")
    if (sn < 0).any():
        raise ValueError("tier_delta_cost: negative short notional")
    return sn * (tier_rate - base_rate) / ANN


LADDER_050_100_300 = {"T0": 0.005, "T1": 0.01, "T2": 0.03}
LADDER_050_200_800 = {"T0": 0.005, "T1": 0.02, "T2": 0.08}


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


# ---- ROUND 2(b): charter tier ladders (champion borrow re-pricing) ----
# T0 == the base rate the committed book is already priced at (a no-op).
LADDER_050_100_300 = {"T0": 0.005, "T1": 0.01, "T2": 0.03}   # 0.5 / 1 / 3 %/yr
LADDER_050_200_800 = {"T0": 0.005, "T1": 0.02, "T2": 0.08}   # R1 calibration 0.5 / 2 / 8 %/yr


def tier_delta_cost(short_notional, base_rate: float, tier_rate: float):
    """Daily borrow delta from re-pricing a SHORT notional stream to a tier rate.

    delta_t = short_notional_t * (tier_rate - base_rate) / 252.
    A tier BELOW the already-charged base yields a NEGATIVE delta (a credit) and is
    never clipped. Fail-closed: negative notional (notional is a short magnitude, >= 0)
    and NaN both raise."""
    sn = short_notional.astype(float)
    if sn.isna().any():
        raise ValueError("short_notional contains NaN")
    if (sn < 0).any():
        raise ValueError("short_notional must be a non-negative magnitude")
    return sn * (tier_rate - base_rate) / ANN


def shortability_pregate(weights, tier_by_name, preserve_gross: bool = True):
    """Hunt-template pre-gate: drop the short leg of un-shortable (NONE) names, then
    optionally re-lever surviving legs so each row's gross is preserved, and compute
    the tiered borrow on surviving shorts.

    Returns (gated_weights, borrow_series, info) where info = dict(dropped, gross_before,
    gross_after, borrow_ann_frac). Fail-closed: unknown tier raises. A `preserve_gross=False`
    leaves survivors unscaled (dropped size just vanishes). NONE names drop ONLY their short
    leg; a long in an un-shortable name is perfectly holdable and stays untouched."""
    if not all(t in TIERS for t in tier_by_name.values()):
        bad = [t for t in tier_by_name.values() if t not in TIERS]
        raise ValueError(f"unknown tier(s) {bad}")
    tier_for = {c: tier_by_name.get(c, "EASY") for c in weights.columns}
    w = weights.copy()
    dropped = [c for c, t in tier_for.items() if t == "NONE"]
    gross_before = w.abs().sum(axis=1)
    for c in dropped:
        w[c] = w[c].clip(lower=0.0)          # drop the short leg only (longs untouched)
    if preserve_gross and dropped:
        gross_after = w.abs().sum(axis=1)
        # scale survivors per row so gross is preserved; guard divide-by-zero (all-dropped row)
        scale = gross_before.div(gross_after.replace(0.0, np.nan)).fillna(0.0)
        w = w.mul(scale, axis=0)

    # borrow on surviving shorts (post-relever notional)
    borrow = pd.Series(0.0, index=weights.index, dtype=float)
    for c, t in tier_for.items():
        if t == "NONE":
            continue
        shorts = (-w[c].clip(upper=0.0))
        borrow = borrow + shorts * TIERS[t] / ANN
    an = weights.abs().sum(axis=1)
    info = {"dropped": dropped, "gross_before": float(gross_before.replace(0.0, np.nan).mean())
            if (gross_before != 0).any() else 0.0,
            "gross_after": float(w.abs().sum(axis=1).replace(0.0, np.nan).mean())
            if (w.abs().sum(axis=1) != 0).any() else 0.0,
            "borrow_ann_frac": float(borrow.mean() * ANN)}
    return w, borrow, info
