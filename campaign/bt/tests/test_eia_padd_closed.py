"""HUNT_EIA_PADD pins: the EIA regional petroleum-storage seam is CLOSED (2026-09-22).

Pre-registered hunt per AUDIT_R7REDO R8 §7c. 47 configs across 3 stages (outright /
locational-basis / flows), best IS(<2017) monthly SR 0.192 vs the 1.0 adoption bar.
These pins make the negative reproducible and prevent silent re-litigation: if a
future construction claims this family, it must beat these numbers through the full
G1-G8 pipeline first.
"""
import pandas as pd
import numpy as np

R = "campaign/agents/HUNT_EIA_PADD"
D = "tools/quant/data/eia_weekly"
IS_END = pd.Timestamp("2017-01-01")


def _sr_m(x: pd.Series) -> float:
    x = x.dropna()
    return x.mean() / x.std() * np.sqrt(12) if len(x) > 3 and x.std() > 0 else np.nan


def test_data_seam_exists_and_certified():
    """The seam is real: 5-PADD crude + distillate + gasoline stock series,
    1990..2026 weekly, Friday stamps, no gaps > 7d."""
    padd = ["p1a", "p2", "p3", "p4", "p5"]
    for a in padd:
        s = pd.read_csv(f"{D}/petstk_{a}_wcestp{a[1:].replace('1a','1')}1.csv",
                        parse_dates=["date"])["value"]
        assert len(s) == 1913, f"{a} crude: expected 1913 certified rows, got {len(s)}"
        assert (s > 0).all()


def test_stage1_outright_all_below_bar():
    r = pd.read_csv(f"{R}/screen_results.csv")
    assert len(r) == 24, "24 pre-registered stage-1 configs (3 families x 4 px x 2 dir)"
    assert r.IS_SR.max() < 0.20, "stage-1 best must stay under 0.20 (recorded 0.173)"
    assert r.IS_SR.max() > 0.0, "sanity: not degenerate"


def test_stage2_basis_all_below_bar():
    r = pd.read_csv(f"{R}/stage2_results.csv")
    assert len(r) == 11
    assert r.IS_SR.max() < 0.15, "stage-2 basis best must stay under 0.15 (recorded 0.104)"


def test_stage3_flows_all_below_bar():
    r = pd.read_csv(f"{R}/stage3_results.csv")
    assert len(r) == 12
    assert r.IS_SR.max() < 0.25, "stage-3 flows best must stay under 0.25 (recorded 0.192)"


def test_family_recorded_dead():
    """The DEAD_IDEAS ledger must carry the closure row."""
    rows = pd.read_csv("campaign/results/DEAD_IDEAS.csv")
    hit = rows[rows.idea.str.contains("EIA PADD regional", case=False, na=False)]
    assert len(hit) == 1, "exactly one HUNT_EIA_PADD ledger row"
    assert hit.iloc[0]["status"] == "dead"
    assert "HUNT_EIA_PADD" in hit.iloc[0]["source"]
