"""V7.1 OOS-DECAY MONITOR TDD — pins the post-act health gate (2026-09-29).

The V7.1 monitor applies the SAME pre-committed rule as the V7.0 monitor (pinned in
test_v7_oos_decay_monitor.py) to the post-act book, with the governance-required
retired-sleeve semantics of V71_REPLICATION_SPEC.md §7: sleeves with w == 0 (the 2
ACTED-ON HARD stops) are reported for health tracking but excluded from the live
fail-close. These tests pin:
(1) the report is produced with 20 sleeves, 18 held, 2 retired (the act invariant);
(2) exit 0 with 0 HARD stops among held sleeves (the act cleared the fail-close);
(3) the rule arithmetic on held sleeves matches the independent reference derivation;
(4) the retired sleeves' health is still visible in the report (trail2y SR present);
(5) the monitor never mutates the V7.1 weights or ledger.
"""
import os, json, subprocess, sys
import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OD = os.path.join(ROOT, "work_backtest_oos")
SCRIPT = os.path.join(OD, "v71_oos_decay_monitor.py")
IS_END = pd.Timestamp("2017-01-01")


def run_monitor():
    cp = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    return cp


def _sr(ser):
    ser = ser.dropna()
    return ser.mean() / ser.std() * np.sqrt(12)


def test_monitor_runs_and_writes_reports():
    cp = run_monitor()
    assert os.path.exists(os.path.join(OD, "V71_OOS_DECAY_REPORT.csv"))
    assert os.path.exists(os.path.join(OD, "V71_OOS_DECAY_REPORT.json"))
    with open(os.path.join(OD, "V71_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["n_sleeves"] == 20
    assert j["n_held"] == 18
    assert j["n_retired"] == 2
    assert set(j["retired_sleeves"]) == {"FXD1_KRWTRI_raw_daily.csv", "crossasset_rev_L8.csv"}
    assert j["rule"]["retired_rule"].startswith("w == 0 sleeves are reported")


def test_exit_zero_no_hard_stops_among_held():
    """The act cleared the live fail-close: 0 HARD stops among the 18 held sleeves."""
    cp = run_monitor()
    with open(os.path.join(OD, "V71_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["n_hard"] == 0
    assert cp.returncode in (0, 2, 3)
    # with no hard stops and no stale sleeves the runner must exit 0
    if j["n_hard"] == 0 and j["freshness"]["n_stale"] == 0:
        assert cp.returncode == 0


def test_retired_health_still_visible():
    """The 2 retired sleeves keep their measured trail2y SR in the report (recovery watch)."""
    df = pd.read_csv(os.path.join(OD, "V71_OOS_DECAY_REPORT.csv"))
    ret = df[df["retired"] == True]
    assert len(ret) == 2
    for _, r in ret.iterrows():
        assert pd.notna(r["trail2y_sr"])
        # both stopped sleeves were HARD (trail2y < 0) when acted on; they stay negative
        # until their data recovers — this pin re-validates openly if they recover
        assert r["trail2y_sr"] < 0, (r["sleeve"], r["trail2y_sr"])
        assert not r["hard"], "retired sleeve must not be HARD-fail the live gate"


def test_classification_matches_reference_on_held_sleeves():
    """Independent re-derivation of the rule on held sleeves (same as the V7.0 pin)."""
    df = pd.read_csv(os.path.join(OD, "V71_OOS_DECAY_REPORT.csv"))
    w_df = pd.read_csv(os.path.join(OD, "OPT_20V71_weights.csv"), index_col=0)
    by = {os.path.basename(k): v for k, v in w_df["w"].items()}
    for _, row in df[df["retired"] == False].iterrows():
        rel = [k for k in w_df.index if os.path.basename(k) == row["sleeve"]][0]
        d = pd.read_csv(os.path.join(ROOT, rel), index_col=0)
        d.index = pd.to_datetime(d.index)
        c = "ret" if "ret" in d.columns else d.columns[0]
        m = (1 + d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()).resample("ME").prod() - 1
        oos = m[m.index >= IS_END].fillna(0.0)
        trail = oos.tail(24)
        full = _sr(oos)
        t = _sr(trail)
        ratio = t / full if full > 1e-12 else 0.0
        w = by[row["sleeve"]]
        assert row["hard"] == bool(t < 0), (row["sleeve"], "hard")
        assert row["decay"] == bool(ratio < 0.8), (row["sleeve"], "decay")
        assert row["advisory_prune"] == bool(ratio < 0.8 and w > 0.10), (row["sleeve"], "advis")


def test_weights_never_mutated_by_monitor():
    """The monitor is read-only on weights/ledger — it must not alter any V7.1 artifact."""
    for artifact in ("OPT_20V71_weights.csv", "OPT_20V71_FULL_LEDGER.csv"):
        p = os.path.join(OD, artifact)
        with open(p) as f:
            before = f.read()
        run_monitor()
        with open(p) as f:
            after = f.read()
        assert before == after, artifact
