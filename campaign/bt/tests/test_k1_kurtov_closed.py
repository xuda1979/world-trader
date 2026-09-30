"""Pins for K1-KURTOV (2026-09-30): inverse-kurtosis overlay on the V7.1
champion — REJECT (GOAL5DIR action D closed). Brace-free; offline."""
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
KOV = os.path.join(HERE, "..", "..", "agents", "K1_KURTOV_results")
DEAD = os.path.join(HERE, "..", "..", "results", "DEAD_IDEAS.csv")


def test_three_preregistered_arms():
    res = pd.read_csv(os.path.join(KOV, "k1_kurtov_results.csv"))
    assert sorted(res.K) == [126, 252, 378]
    assert len(res) == 3


def test_all_arms_reject():
    """Headline negative: every pre-registered arm fails G1 (materiality) and
    G6 (sign consistency) on OOS."""
    res = pd.read_csv(os.path.join(KOV, "k1_kurtov_results.csv"))
    assert (~res.G1).all()
    assert (~res.G6).all()
    assert (res.oos_edge < 0).all()


def test_overlay_deepens_dd_and_lifts_ann():
    """The structural finding: the kurtosis overlay concentrates risk — OOS DD
    deepens on every arm (champion -3.16%), while ann rises (it is paid for the
    extra tail risk, not alpha)."""
    res = pd.read_csv(os.path.join(KOV, "k1_kurtov_results.csv"))
    assert (res.oos_mdd < -0.0316).all()      # every arm deeper than champion
    assert (res.oos_mdd <= -0.050).all()      # and materially so (>=5%)
    assert (res.oos_ann > 0.3072).all()       # higher ann everywhere


def test_champion_reference_pinned():
    """Champion OOS SR from the report header == canonical 3.6718 (the V7.1
    OOS SR, reproduce_v71 tol 0.01)."""
    rep = open(os.path.join(KOV, "K1_KURTOV_REPORT.md")).read()
    assert "SR 3.6718" in rep


def test_dead_ideas_row():
    df = pd.read_csv(DEAD)
    row = df[df.idea.str.contains("K1-KURTOV inverse-kurtosis overlay")]
    assert len(row) == 1
    assert row.iloc[0]["status"] == "dead"
    assert row.iloc[0]["source"] == "K1_KURTOV"


def test_prereg_before_results():
    assert os.path.getmtime(os.path.join(KOV, "PREREGISTRATION.md")) <= \
        os.path.getmtime(os.path.join(KOV, "k1_kurtov_results.csv")) + 5
    pre = open(os.path.join(KOV, "PREREGISTRATION.md")).read()
    assert "126, 252, 378" in pre
    for g in ("G1", "G2", "G3", "G4", "G5", "G6"):
        assert g + "." in pre
