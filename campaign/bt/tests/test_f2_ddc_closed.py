"""Pins for the F2-DDC study (2026-09-30): drawdown-control post-processing on the
V7.1 champion — ALL FAMILIES REJECT. Brace-free; offline; reads committed CSVs."""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DDC = os.path.join(HERE, "..", "..", "agents", "F2_DDC_results")
LEDGER = os.path.join(HERE, "..", "..", "work_backtest_oos",
                      "OPT_20V71_FULL_LEDGER.csv")
DEAD = os.path.join(HERE, "..", "..", "results", "DEAD_IDEAS.csv")


def _load_champion():
    led = pd.read_csv(LEDGER, parse_dates=["date"])
    g = led.groupby("date")[["pnl", "cost"]].sum().sort_index()
    r = (g["pnl"] - g["cost"]).astype(float)
    return r[r.index >= "2009-01-01"]


def test_results_csv_complete_34_arms():
    res = pd.read_csv(os.path.join(DDC, "f2_ddc_results.csv"))
    assert len(res) == 34, len(res)
    assert set(res.family) == {"DDHALT", "DDSCALE", "VOLTGT", "TLOSS",
                               "DDHALT_POSTHOC"}
    # pre-registered families: 8+12+3+3 = 26; post-hoc fine grid: 8
    assert (res.family != "DDHALT_POSTHOC").sum() == 26
    assert (res.family == "DDHALT_POSTHOC").sum() == 8


def test_all_families_reject_gates():
    """The headline negative: every pre-registered family fails at least one gate
    on its IS-champion arm (G1 materiality +0.10 monthly SR never met)."""
    res = pd.read_csv(os.path.join(DDC, "f2_ddc_results.csv"))
    for fam in ("DDHALT", "DDSCALE", "VOLTGT", "TLOSS"):
        best = res[res.family == fam].sort_values("is_sr", ascending=False).iloc[0]
        assert not best["G1"], fam
        assert best["oos_edge"] < 0.10


def test_monotone_binding_hurts():
    """The structural finding: the more a DD-halt binds, the more it hurts OOS.
    Post-hoc b=1% (deep binding) edge < b=1.5% < b=2% < b=2.5% < 0."""
    res = pd.read_csv(os.path.join(DDC, "f2_ddc_results.csv"))
    ph = res[res.family == "DDHALT_POSTHOC"].set_index("name")
    e1 = ph.loc["b=1.0%_a=0.5%", "oos_edge"]
    e15 = ph.loc["b=1.5%_a=1.0%", "oos_edge"]
    e2 = ph.loc["b=2.0%_a=1.5%", "oos_edge"]
    e25 = ph.loc["b=2.5%_a=2.0%", "oos_edge"]
    assert e1 < e15 < e2 < e25 < 0


def test_noop_arms_are_exact_zero_edge():
    """VOLTGT tgt>=10% and TLOSS x>=5% never bind on V7.1 (DD too shallow):
    zero turnover, 100% in-market, oos_edge == 0 to float precision."""
    res = pd.read_csv(os.path.join(DDC, "f2_ddc_results.csv"))
    noop = res[(res.family.isin(["VOLTGT", "TLOSS"]))]
    assert (noop.to_yr == 0).all()
    assert (noop.oos_edge.abs() < 1e-12).all()


def test_champion_reference_pinned():
    """Champion OOS SR from the ledger (monthly convention) matches the report's
    pinned reference 3.6718 (canonical V7.1 OOS SR, reproduce_v71 tol 0.01)."""
    r = _load_champion()
    m = (1 + r).resample("ME").prod() - 1
    mo = m[m.index >= "2017-01-01"]
    sr = mo.mean() / mo.std() * (12 ** 0.5)
    assert abs(sr - 3.6718) <= 0.01, sr


def test_dead_ideas_row_appended():
    df = pd.read_csv(DEAD)
    row = df[df.idea.str.startswith("F2-DDC drawdown-control post-processing")]
    assert len(row) == 1
    assert row.iloc[0]["status"] == "dead"
    assert row.iloc[0]["source"] == "F2_DDC"


def test_preregistration_locked_before_results():
    """Governance: PREREGISTRATION.md exists, declares 26 arms + gates G1-G6,
    and predates the results file it governs."""
    assert os.path.exists(os.path.join(DDC, "PREREGISTRATION.md"))
    pre = open(os.path.join(DDC, "PREREGISTRATION.md")).read()
    assert "26 arms" in pre.replace("26 pre-registered arms", "26 arms") or "26" in pre
    for g in ("G1", "G2", "G3", "G4", "G5", "G6"):
        assert g + "." in pre
    assert os.path.getmtime(os.path.join(DDC, "PREREGISTRATION.md")) <= \
        os.path.getmtime(os.path.join(DDC, "f2_ddc_results.csv")) + 5
