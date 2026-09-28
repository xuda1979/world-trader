"""CAMP_COST R3 (b) — turnover attribution tests.

Standard: champion cost = sum_i |dW_i| * 6.4bps (one-side, FULL dW, committed champion
convention, verified R1). Attribution must be EXACT: per-sleeve shares must sum to 100% of
measured cost (no residual), annual bps must reconcile to the champion's own cost stream,
and the sum over sleeves + borrow must reconcile to the champion net series.
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r3")

ATTRIB = f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/work_r3/turnover_attribution.csv"
BPS_STD = 6.4


def _table(**kw):
    import turnover_attribution as ta
    return ta.build_attribution(**kw)


def test_attribution_table_exists_and_complete():
    t = _table()
    assert os.path.exists(ATTRIB), "turnover_attribution.csv missing"
    assert len(t) == 12, f"expected 12 champion sleeves, got {len(t)}"
    for col in ("sleeve", "turnover_sum", "cost_bps_yr", "share_pct", "rank"):
        assert col in t.columns, f"missing column {col}"


def test_shares_sum_to_100_and_ranks_consistent():
    t = _table(print_table=False)
    assert abs(t.share_pct.sum() - 100.0) < 1e-9, (
        f"shares sum to {t.share_pct.sum():.6f}% — attribution must be exact, no residual")
    assert t.share_pct.min() >= -1e-12, "negative share (impossible: |dW| >= 0)"
    assert list(t.sort_values("share_pct", ascending=False)["rank"]) == list(t["rank"]), (
        "rank column inconsistent with share_pct ordering")


def test_cost_bps_reconciles_to_champion_cost_stream():
    """sum_i turnover_i * 6.4bps must equal the champion's measured cost stream
    (sum over days of |dW| * 6.4e-4), within float noise."""
    t, total_cost_bps = _table(return_total=True, print_table=False)
    # recomputed directly from the committed champion weights
    import campaign.scripts.rawew13v2_build as rb
    _, _, _, to_b, _df = rb.build()
    to = to_b.iloc[1:]  # day-1 entry uncharged (builder convention)
    # annual bps: avg daily |dW| * 252 trading days * 6.4 bps per unit turnover
    measured_bps = float(to.sum() / len(to) * 252 * BPS_STD)
    assert abs(total_cost_bps - measured_bps) / measured_bps < 1e-9, (
        f"attribution total {total_cost_bps:.3f} vs measured {measured_bps:.3f} bps/yr")


def test_top5_drivers_named_and_sane():
    t = _table(print_table=False)
    top5 = t.sort_values("share_pct", ascending=False).head(5).sleeve.tolist()
    assert len(top5) == 5
    assert t.share_pct.head(5).sum() > 25.0, "top-5 must dominate (13 slots, family-heavy)"


def test_attribution_matches_corrected_pool_too():
    """The corrected (costfixed) 12-sleeve pool under the CURRENT production recipe
    (correlation-aware fit_relw + costfix brwt sleeves + nav.shift(1) @1.6x, rawew13v2_build)
    must reconcile to the per-sleeve attribution table within 10%.

    (was: rebuilt via stale work_r3/candidates.py max(SR,0)^P — the RETIRED rule — which
    inflated turnover to 16.61 vs 14.20, a 16.95% artifact of the stale rule, not of the
    corrected pool. Using the production builder the delta is ~machine-zero.)"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("rawew13v2", f"{ROOT}/campaign/scripts/rawew13v2_build.py")
    rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)
    assert "brwt15" not in rb.NAMES, "ITER19: brwt15 must be pruned from the champion pool"
    _, _, _, to_prod, _ = rb.build()  # 12-sleeve corrected-costfix champion, current weights
    to13 = to_prod.iloc[1:]           # drop day-1 (entry uncharged), same convention
    t = _table(print_table=False)
    delta = abs(to13.sum() - t.turnover_sum.sum()) / t.turnover_sum.sum()
    assert delta < 0.10, f"corrected-pool champion turnover differs by {delta*100:.2f}%"
    assert delta < 1e-9, f"corrected-pool champion turnover should be machine-exact: {delta:.2e}"
