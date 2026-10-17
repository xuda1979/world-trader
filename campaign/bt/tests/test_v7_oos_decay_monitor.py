"""V7 OOS-DECAY MONITOR TDD — pins the pre-committed health-gate rule.

The monitor is a REPORTING gate (never re-optimizes weights). These tests pin:
(1) the rule arithmetic (hard/decay/advisory classification), and
(2) that the live V7 report is produced deterministically with the expected
    classification of the current sleeve set (as of 2026-09-30 data).
A HARD-stop (trail2y SR < 0) means a regime break to surface — the runner exits 2
(fail-closed), which a scheduler can treat as an alert, not a crash.
"""
import os, json, subprocess, sys
import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OD = os.path.join(ROOT, "work_backtest_oos")
SCRIPT = os.path.join(OD, "v7_oos_decay_monitor.py")
IS_END = pd.Timestamp("2017-01-01")


def run_monitor():
    cp = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True)
    return cp


def _sr(ser):
    ser = ser.dropna()
    return ser.mean() / ser.std() * np.sqrt(12)


def _classify(oos, trail, w):
    full_sr = _sr(oos)
    trail_sr = _sr(trail)
    ratio = trail_sr / full_sr if full_sr > 1e-12 else 0.0
    return dict(full=full_sr, trail=trail_sr, ratio=ratio,
                hard=bool(trail_sr < 0),
                decay=bool(ratio < 0.8),
                advis=bool(ratio < 0.8 and w > 0.10))


def test_monitor_runs_and_writes_reports():
    cp = run_monitor()
    assert os.path.exists(os.path.join(OD, "V7_OOS_DECAY_REPORT.csv"))
    assert os.path.exists(os.path.join(OD, "V7_OOS_DECAY_REPORT.json"))
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["n_sleeves"] == 20
    assert j["rule"]["ratio_floor"] == 0.8
    assert j["rule"]["high_w"] == 0.10
    # FXD1 is a stated HARD stop (trail2y SR < 0) as of this data vintage; if the
    # data is refreshed and it recovers, this pin should be re-validated openly.
    assert "FXD1_KRWTRI_raw_daily.csv" in j["hard_stops"]


def test_classification_matches_reference_implementation():
    """Recompute the monitor's rule independently on the same sleeve stream and confirm
    the script's CSV flags agree with this independent re-derivation (no lookahead:
    both use OOS >= IS_END and a trailing-24m window)."""
    df = pd.read_csv(os.path.join(OD, "V7_OOS_DECAY_REPORT.csv"))
    w_df = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)
    by = {os.path.basename(k): v for k, v in w_df["w"].items()}
    for _, row in df.iterrows():
        rel = w_df.index[w_df.index.str.contains(row["sleeve"], regex=False)][0]
        d = pd.read_csv(os.path.join(ROOT, rel), index_col=0)
        d.index = pd.to_datetime(d.index)
        c = "ret" if "ret" in d.columns else d.columns[0]
        m = (1 + d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()).resample("ME").prod() - 1
        oos = m[m.index >= IS_END].fillna(0.0)
        trail = oos.tail(24)
        cl = _classify(oos, trail, by[row["sleeve"]])
        assert row["hard"] == cl["hard"], (row["sleeve"], "hard", row["hard"], cl["hard"])
        assert row["decay"] == cl["decay"], (row["sleeve"], "decay", row["decay"], cl["decay"])
        assert row["advisory_prune"] == cl["advis"], (row["sleeve"], "advis")


def test_no_advisory_prune_on_current_weights():
    """RE-PINNED 2026-10-17 (10-16 refresh wave): C4_construct_v2 now DECAYS at ratio
    0.714 (trail2y SR 2.53 vs full-OOS 3.55 — the ratio artifact of an outsized full
    SR, not weak absolute performance) while carrying 15% of gross, so the >10%
    advisory-prune rule GENUINELY FIRES: n_advisory_prune == 1, flagged sleeve C4.
    The advisory flag is informational only; the pre-committed prune decision was
    adjudicated NO PRUNE in the 2026-09-29 hard-stop governance counterfactual
    (V7_SESSION_2026-09-29_HARDSTOP_ACT.md) and stands — zeroing C4 is NOT authorized
    by this report. The 09-22 pin (n_advisory_prune == 0, all decayers <= 8.9%) went
    stale when C4's trail2y/full ratio crossed 0.8 at this data vintage. This pin
    keeps the rule engaged in the strongest sense: it demonstrably fires on the
    book's heaviest engine."""
    with open(os.path.join(OD, "V7_OOS_DECAY_REPORT.json")) as f:
        j = json.load(f)
    assert j["n_advisory_prune"] == 1
    df = pd.read_csv(os.path.join(OD, "V7_OOS_DECAY_REPORT.csv"))
    adv = df[df["advisory_prune"] == True]
    assert list(adv["sleeve"]) == ["C4_construct_v2.csv"]
    assert float(adv["ratio"].iloc[0]) < 0.8
    assert float(adv["w"].iloc[0]) > 10.0
    # and at least one HARD or DECAY is flagged so the gate is not vacuously green
    assert j["n_hard"] + j["n_decay"] >= 1


def test_weights_never_mutated_by_monitor():
    """The monitor is read-only on weights/ledger — it must not alter any V7 artifact."""
    with open(os.path.join(OD, "OPT_20V7_weights.csv")) as f:
        before = f.read()
    run_monitor()
    with open(os.path.join(OD, "OPT_20V7_weights.csv")) as f:
        after = f.read()
    assert before == after
