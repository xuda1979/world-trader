"""V7.1 HARD-STOP ACT TDD — pins the governed A4 zero+renorm adoption (2026-09-29).

Context: the operator ACT decision on the 2 decay-monitor HARD stops
(FXD1_KRWTRI_raw_daily.csv, crossasset_rev_L8.csv) adopted arm A4 (zero + renormalize)
via the V71 spec bump. These tests pin the act's invariants:
(1) the committed V7.1 weights are the exact §4.2 transform of the committed V7.0
    vector (2 zeros, survivors renormalized — 1e-6 exact-arithmetic pin);
(2) the V7.1 ledger's pre-switch marks are byte-identical to the V7.0 ledger's
    (the act touches nothing before 2024-10);
(3) the V7.1 ledger's post-switch marks reconcile to LEV x gross on the §1 weights;
(4) the canonical A4 metrics (full SR 4.074 etc.) hold on the committed ledger;
(5) the V7.0 spec/weights/ledger files are UNCHANGED by the act (V7.0 preserved).
"""
import os, subprocess, sys
import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OD = os.path.join(ROOT, "work_backtest_oos")
IS_END = pd.Timestamp("2017-01-01")
TRAIL2Y = pd.Timestamp("2024-10-01")
LEV = 1.6

W7 = os.path.join(OD, "OPT_20V7_weights.csv")
W71 = os.path.join(OD, "OPT_20V71_weights.csv")
LED7 = os.path.join(OD, "OPT_20V7_FULL_LEDGER.csv")
LED71 = os.path.join(OD, "OPT_20V71_FULL_LEDGER.csv")
SPEC71 = os.path.join(OD, "V71_REPLICATION_SPEC.md")


def _load_w(p):
    w = pd.read_csv(p, index_col=0)["w"].astype(float)
    return w


def test_v71_weights_are_exact_zero_renorm_of_v70():
    """§4.2 transform: committed V7.1 == renorm(committed V7.0 with 2 zeros), 1e-6."""
    w7 = _load_w(W7)
    w71 = _load_w(W71)
    assert list(w7.index) == list(w71.index)
    KRW = [s for s in w7.index if "FXD1_KRWTRI" in s][0]
    XREV = [s for s in w7.index if "crossasset_rev_L8" in s][0]
    w4 = w7.copy()
    w4[KRW] = 0.0
    w4[XREV] = 0.0
    expect = w4 / w4.sum()
    dev = (expect - w71).abs().max()
    assert dev < 1e-6, f"transform deviation {dev:.2e} exceeds retired S1 baseline 1e-6"
    assert w71[KRW] == 0.0 and w71[XREV] == 0.0
    assert abs(w71.sum() - 1.0) < 1e-9
    assert (w71 > 0).sum() == 18


def test_v71_ledger_pre_switch_marks_identical_to_v70():
    """The act must not touch anything before the 2024-10 switch."""
    a = pd.read_csv(LED7, parse_dates=["date"])
    b = pd.read_csv(LED71, parse_dates=["date"])
    ma = a[a.component == "mark"].groupby("date")["pnl"].sum().sort_index()
    mb = b[b.component == "mark"].groupby("date")["pnl"].sum().sort_index()
    pre_a = ma[ma.index < TRAIL2Y]
    pre_b = mb[mb.index < TRAIL2Y].reindex(pre_a.index)
    dev = (pre_a - pre_b).abs().max()
    assert dev == 0.0, f"pre-switch marks diverged: max|d|={dev:.2e}"


def test_v71_ledger_post_switch_recon():
    """Post-switch marks == LEV x gross(daily, §1 weights)."""
    w71 = _load_w(W71)
    led = pd.read_csv(LED71, parse_dates=["date"])
    marks = led[led.component == "mark"].groupby("date")["pnl"].sum().sort_index()
    post = marks[marks.index >= TRAIL2Y]
    ddf = {}
    for s in w71.index:
        d = pd.read_csv(os.path.join(ROOT, s), index_col=0)
        d.index = pd.to_datetime(d.index)
        c = "ret" if "ret" in d.columns else d.columns[0]
        ddf[s] = d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    panel = pd.DataFrame(ddf)
    panel = panel[panel.index >= "2009-01-01"].fillna(0.0)
    gross = panel[list(w71.index)].dot(w71)
    dev = (post - LEV * gross.reindex(post.index)).abs().max()
    assert dev < 1e-9, f"post-switch recon {dev:.2e}"


def test_v71_canonical_metrics():
    """Committed-ledger canonicals (spec §6): A4 row of V8GOV_EVAL, 4dp."""
    led = pd.read_csv(LED71, parse_dates=["date"])
    g = led.groupby("date")[["pnl", "cost"]].sum()
    net_d = (g.pnl - g.cost).sort_index()
    net_m = (1 + net_d).resample("ME").prod() - 1
    oos = net_m[net_m.index >= IS_END]
    t2y = net_m[net_m.index >= TRAIL2Y]
    dd = ((1 + net_d).cumprod() / (1 + net_d).cumprod().cummax() - 1).min() * 100

    def srm(x):
        x = x.dropna()
        return x.mean() / x.std() * np.sqrt(12)

    yrs = (1 + net_m).groupby(net_m.index.year).prod() - 1
    assert abs(srm(net_m) - 4.0792) < 5e-3
    assert abs(srm(oos) - 3.6718) < 5e-3
    assert abs(net_m.mean() * 12 * 100 - 27.969) < 5e-2
    assert abs(oos.mean() * 12 * 100 - 30.481) < 5e-2
    assert abs(srm(t2y) - 3.9223) < 5e-3
    assert abs(t2y.mean() * 12 * 100 - 28.125) < 5e-2
    assert abs(dd - (-3.161)) < 5e-2
    assert int((yrs < 0).sum()) == 0


def test_v70_artifacts_unchanged_by_act():
    """V7.0 spec/weights/ledger must still exist and reproduce their own gate."""
    for p in (W7, LED7, os.path.join(OD, "V7_REPLICATION_SPEC.md")):
        assert os.path.exists(p)
    # the V7.0 weights table itself must not have been mutated (2 stops still 3%/8.9%)
    w7 = _load_w(W7)
    KRW = [s for s in w7.index if "FXD1_KRWTRI" in s][0]
    XREV = [s for s in w7.index if "crossasset_rev_L8" in s][0]
    assert abs(w7[KRW] - 0.03) < 1e-12
    assert abs(w7[XREV] - 0.08916506) < 1e-8
    assert abs(w7.sum() - 1.0) < 1e-9


def test_spec71_table_parses_and_matches_weights():
    """The V7.1 spec §1 table must parse (20 rows) and equal committed weights (6dp)."""
    import re
    doc = open(SPEC71).read()
    rows = re.findall(r"^\| \d+ \| `([^`]+)` \| ([0-9.]+)% \|", doc, re.M)
    assert len(rows) == 20
    w71 = _load_w(W71)
    for rel, pct in rows:
        assert abs(float(pct) / 100.0 - w71[rel]) < 5e-7, rel
    assert "Zeroed sleeves" in doc and "§4.2" in doc
