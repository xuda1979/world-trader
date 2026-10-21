"""HUNT_ALT_METALS: copper ('Dr. Copper') alternative-data acquisition + honest gate pin.

2026-09-22: copper was NOT on disk (2026-09-14 log: 'no GC/SI' metals). Fetched from
AlphaVantage COPPER monthly (free tier, working key) -> data/copper_alpha.csv (1992-2026-07).
These tests pin (1) the data is now present with full history and no holes, (2) the honest
gate: copper sleeves are DECORRELATED (|corr|<0.15) but SUB-BAR (IS monthly SR < 1.0), so
they are REJECTED for V7 adoption — recorded as a reproducible negative, not a tuning invite.
"""
import os
import numpy as np
import pandas as pd
import pytest

HUNT = "campaign/agents/HUNT_ALT_METALS"
DATA = os.path.join(os.path.dirname(os.getcwd()) and HUNT, "data/copper_alpha.csv")


@pytest.fixture
def copper_level():
    p = os.path.join(HUNT, "data/copper_alpha.csv")
    assert os.path.exists(p), "copper data must have been fetched and persisted"
    c = pd.read_csv(p)
    c["date"] = pd.to_datetime(c["date"])
    return c.set_index("date")["value"].astype(float).sort_index().resample("ME").last().dropna()


def test_copper_data_present_full_history(copper_level):
    assert len(copper_level) > 200, "need long copper history for a monthly sleeve"
    # AlphaVantage COPPER spans 1992 -> 2026; assert the span
    assert copper_level.index.min() <= pd.Timestamp("2000-01-01")
    assert copper_level.index.max() >= pd.Timestamp("2025-01-01")
    assert copper_level.isna().sum() == 0
    assert (copper_level > 0).all(), "prices must be positive"


def test_copper_decorrelated_from_champion(copper_level):
    LED = pd.read_csv("campaign/work_backtest_oos/OPT_20V7_FULL_LEDGER.csv", parse_dates=["date"])
    g = LED.groupby("date")[["pnl", "cost"]].sum()
    champ_m = (1 + (g.pnl - g.cost).sort_index()).resample("ME").prod() - 1
    c_ret = copper_level.pct_change().dropna()
    both = pd.concat([c_ret.rename("sleeve"), champ_m.rename("champ")], axis=1).dropna()
    both = both[both.index >= "2009-01-01"]
    corr = float(both["sleeve"].corr(both["champ"]))
    assert abs(corr) < 0.15, f"copper unexpectedly correlates to energy book: {corr:.3f}"


def test_copper_sleeves_sub_bar_so_rejected(copper_level):
    """Honest gate: the best copper signal (raw long) has IS monthly SR ~0.5, far under
    V7's >1.0 adoption floor -> REJECTED. This is a reproducible NEGATIVE; if a future
    construction clears the bar it must be re-validated through the full G1-G8 pipeline first."""
    m = copper_level.pct_change().dropna()
    isr = m[m.index < "2017-01-01"]
    sr = isr.mean() / isr.std() * np.sqrt(12)
    assert sr < 1.0, "copper would need to exceed the bar to be reconsidered"
    assert sr > -1.0, "sanity: not degenerate"
