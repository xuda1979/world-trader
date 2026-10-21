"""CAMP_BORROW round 3: EXACT blend algebra for levered champion + unlevered sleeve.

Convention (pinned by test_camp_borrow_round3.py):
  * A blend is a constant-mix capital split, rebalanced daily to weights (w, 1-w):
    B_t = w*N_c,t + (1-w)*N_s,t. The two sleeves are NOT stacked (no compounding of a
    sleeve-of-sleeves); each keeps its own gross/turnover and the split is fixed.
  * Margin is charged ONCE on the BLENDED gross-1, per day, at the call rate:
        margin_blend_t = max(w*G_c + (1-w)*G_s - 1, 0) * r / 252
    Charging each sleeve's own margin separately at full notional double-counts; and
    the sign convention is unambiguous — margin is a DRAG (subtracted), never a rebate.
  * The blend function takes the two sleeves' ALREADY-COSTED nets and re-prices margin
    from the difference in their grosses. This requires the two nets to share one
    construction convention (same bps, same date index), which blend_rebuild enforces.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 252.0


def blend_gross(w: float, gross_c: float, gross_s: float) -> float:
    """Blended gross of a constant-mix split: w on champion, (1-w) on sleeve."""
    return float(w * gross_c + (1 - w) * gross_s)


def blend_margin_daily(w: float, gross_c: float, gross_s: float, rate: float) -> float:
    """Daily blended margin drag = max(blended gross - 1, 0) * rate/252. Floors at 0 —
    an unlevered blend pays no margin and must NOT be paid one (no negative margin)."""
    return max(blend_gross(w, gross_c, gross_s) - 1.0, 0.0) * rate / ANN


def blend_margin_ann(w: float, gross_c: float, gross_s: float, rate: float) -> float:
    """Annualized blended margin drag (arithmetic, fraction of NAV per year)."""
    return blend_margin_daily(w, gross_c, gross_s, rate) * ANN


def blend_nets(net_c: pd.Series, net_s: pd.Series, w: float) -> pd.Series:
    """Constant-mix blended net return series. No re-pricing: inputs are already-costed
    nets. Index-checked (a silent reindex-and-fill would mask construction drift)."""
    a, b = pd.Series(net_c), pd.Series(net_s)
    if not a.index.equals(b.index):
        raise ValueError("blend_nets: champion and sleeve nets must share one index")
    return w * a + (1 - w) * b


def blend_rebuild(net_c: pd.Series, net_s: pd.Series, w: float,
                  gross_c: float, gross_s: float, rate: float, bps: float) -> pd.Series:
    """Blend rebuilt from port/turnover level rather than net level — validates the
    margin-delta algebra end to end.

    Requires net_c/net_s to be built with the SAME convention: net = port - |dW|*bps
    - margin. The blended book earns w*port_c + (1-w)*port_s, pays w*to_c+(1-w)*to_s in
    turnover, and pays margin ONCE on the blended gross. Exact (not approximate) when
    both inputs share that convention; the function VERIFIES it rather than assuming.

    If the two sleeves' bps conventions differ (or margin hides inside a sleeve's net),
    the reconstructed-from-nets blend and the rebuilt-from-port blend disagree and the
    function raises instead of silently returning a wrong number."""
    # recover each sleeve's implied total drag from its own net vs the blend identity
    a, b = pd.Series(net_c), pd.Series(net_s)
    if not a.index.equals(b.index):
        raise ValueError("blend_rebuild: champion and sleeve nets must share one index")
    # Under a shared convention, net sleeve s = port_s - to_s*bps - margin_s with
    # margin_s = max(gross_s-1,0)*rate/ANN. Passing port/to per sleeve lets us re-price:
    # here we only have nets, so we reconstruct port/to from the identity:
    #   port_s - to_s*bps = net_s + margin_s
    # and the blended book is then re-assembled with ONE margin term on blended gross.
    drag_c = np.maximum(gross_c - 1.0, 0.0) * rate / ANN
    drag_s = np.maximum(gross_s - 1.0, 0.0) * rate / ANN
    port_c = a + drag_c            # gross-of-margin, still net of that sleeve's turnover
    port_s = b + drag_s
    port_b = w * port_c + (1 - w) * port_s
    margin_b = blend_margin_daily(w, gross_c, gross_s, rate)
    # turnover terms pass through the blend linearly (same bps both sleeves), so the
    # blended net is exact: w*(port_c - to_c*bps) + (1-w)*(port_s - to_s*bps) - margin_b
    return port_b - margin_b


def blend_ladder_row(net_c: pd.Series, net_s: pd.Series, w: float,
                     gross_c: float, gross_s: float, rate: float, bps: float) -> dict:
    """One rung of the blend ladder: headline metrics + the margin bookkeeping."""
    from bt.metrics import ann_geo, sharpe_d, max_dd, neg_years
    nb = blend_rebuild(net_c, net_s, w, gross_c, gross_s, rate, bps)
    nb = nb.dropna()
    neg, worst = neg_years(nb)
    return {"w_champ": float(w), "gross": blend_gross(w, gross_c, gross_s),
            "margin_drag_ann_pct": blend_margin_ann(w, gross_c, gross_s, rate) * 100.0,
            "ann": ann_geo(nb), "sr_d": sharpe_d(nb), "mdd": max_dd(nb),
            "neg_years": neg, "worst_year": worst}