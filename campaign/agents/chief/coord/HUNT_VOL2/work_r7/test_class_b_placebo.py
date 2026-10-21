"""HUNT_VOL2 ROUND 7(a) - TDD RED-FIRST unit tests for the Class-B level-matched null
reference implementation (V3 proposal instrument per work_r6/placebo_orthogonal_memo.md;
GATES_CONTRACT_V3 is a PROPOSAL until AUDIT_GATES2 ratifies - nothing here edits gates.py,
zero thresholds move, and a placebo verdict is never an adoption).

RED-first contract: this file was written and run BEFORE work_r7/class_b_placebo.py
existed (collection failure = RED), then GREENed by the implementation.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import class_b_placebo as cb  # noqa: E402  (RED until the module lands)


# ------------------------------------------------------------------- fixtures
def mk_sr(vals, start="2010-01-04"):
    return pd.Series(np.asarray(vals, dtype=float), index=pd.bdate_range(start, periods=len(vals)))


def seeded_champion(n=1500, seed=7):
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0004, 0.007, n)
    r[400:415] -= 0.012   # stress episode 1
    r[900:918] -= 0.010   # stress episode 2
    return mk_sr(r)


# ------------------------------------------------------------- moments / nulls
def test_stream_moments_matches_hand_computed():
    s = mk_sr([0.01, -0.02, 0.03, 0.0, -0.01, 0.02, -0.03, 0.01, 0.0, 0.005] * 10)
    m = cb.stream_moments(s)
    assert abs(m["mean"] - s.mean()) < 1e-15
    assert abs(m["vol"] - s.std(ddof=1)) < 1e-15
    assert abs(m["ac1"] - s.autocorr(1)) < 1e-12
    assert abs(m["skew"] - s.skew()) < 1e-12


def test_level_matched_nulls_preserve_mean_vol_exactly_ac1_skew_approximately():
    rng = np.random.default_rng(11)
    e = rng.normal(0, 0.006, 1200)
    ar = np.empty(1200)
    ar[0] = 0.0
    for t in range(1, 1200):          # AR(1) phi=0.35 positive-mean stream
        ar[t] = 0.35 * ar[t - 1] + e[t] + 0.0004
    ar[::97] += 0.05                  # a few big positives so the stream is skewed
    s = mk_sr(ar)
    m0 = cb.stream_moments(s)
    nulls = cb.level_matched_nulls(s, n=40, block=20, rng=np.random.default_rng(5))
    assert len(nulls) == 40
    for d in nulls:
        md = cb.stream_moments(d)
        assert abs(md["mean"] - m0["mean"]) < 1e-15          # exact re-match (level is NOT the test)
        assert abs(md["vol"] - m0["vol"]) < 1e-15            # exact re-match
        assert abs(md["ac1"] - m0["ac1"]) < 0.15             # block bootstrap preserves approx
        assert abs(md["skew"] - m0["skew"]) < 0.8            # approx (skew-2 spike stream:
        # 13 spike days in 1200 -> draw-level skew is noisy; an iid null would sit ~0)
        assert d.index.equals(s.index)


def test_level_matched_nulls_deterministic_given_seed():
    s = seeded_champion(300, seed=3)
    a = cb.level_matched_nulls(s, n=3, block=20, rng=np.random.default_rng(5))
    b = cb.level_matched_nulls(s, n=3, block=20, rng=np.random.default_rng(5))
    for x, y in zip(a, b):
        assert x.equals(y)


def test_level_matched_nulls_breaks_calendar_alignment():
    """The null must NOT preserve the real stream's day alignment: at least one draw
    differs from the real stream on >30% of days (else it is a no-op, not a null)."""
    s = seeded_champion(600, seed=4)
    nulls = cb.level_matched_nulls(s, n=20, block=20, rng=np.random.default_rng(6))
    frac_diff = [float((d.values != s.values).mean()) for d in nulls]
    assert min(frac_diff) > 0.30


# ------------------------------------------------------------- blend machinery
def test_blend_simple_matches_independent_hand_computation():
    rc = seeded_champion(300, seed=1)
    rs = mk_sr(rng_vals(300, 0.0005, 0.008, seed=2), start=str(rc.index[0].date()))
    rs = rs.reindex(rc.index).fillna(0.0)
    w = 0.10
    got = cb.blend_simple(rc, rs, w, bps=6.4)
    # hand: leg drift from PRIOR-day NAVs, T+1; one-side book turnover = 2*|(1-w) - Wc_prev|
    Wc = (1 - w) * (1 + rc) / ((1 - w) * (1 + rc) + w * (1 + rs))
    to = (2.0 * ((1 - w) - Wc.shift(1))).abs().fillna(0.0)
    want = (1 - w) * rc + w * rs - to * 6.4 / 1e4
    pd.testing.assert_series_equal(got, want, check_exact=False, rtol=1e-12)


def rng_vals(n, mu, sd, seed):
    return np.random.default_rng(seed).normal(mu, sd, n)


# ------------------------------------------------------------ Class-B instrument
def test_timed_candidate_sits_in_right_tail_of_own_null():
    """A candidate whose gain lives in WHEN it earns (earns on champion crisis days) must
    sit at p95+ of its own level-matched null: re-ordering destroys the alignment.
    Champion keeps a positive drift above its crisis drag (else SR<0 and the dSR sign
    convention inverts — variance reduction hurts a negative-SR book)."""
    rng = np.random.default_rng(42)
    n = 1500
    rc_vals = rng.normal(0.0006, 0.0065, n)
    rc_vals[300:318] -= 0.010
    rc_vals[800:820] -= 0.009
    rc_vals[1200:1212] -= 0.011
    rc = mk_sr(rc_vals)
    rs_vals = np.full(n, -0.0002)
    crisis = rc_vals < np.percentile(rc_vals, 4.0)
    rs_vals[crisis] = 0.012 + 0.004 * rng.standard_normal(int(crisis.sum()))
    rs = pd.Series(rs_vals, index=rc.index)
    out = cb.class_b_placebo(rc, rs, w=0.10, n_nulls=200, block=20,
                             rng=np.random.default_rng(123))
    assert out["real_dsr"] > 0
    assert out["real_percentile"] >= 0.95
    assert out["right_tail_p95_pass"] is True
    assert out["n_nulls"] == 200


def test_positive_mean_coin_without_timing_sits_near_center_of_own_null():
    """A pure positive-mean stream (no timing content) is exchangeable with its own
    re-ordered draws: its percentile must NOT sit at p95+ (mean-injection priced OUT)."""
    rc_vals = np.random.default_rng(9).normal(0.0006, 0.0065, 1500)
    rc_vals[400:415] -= 0.011
    rc = mk_sr(rc_vals)
    rs = pd.Series(np.random.default_rng(2024).normal(0.0006, 0.008, len(rc)), index=rc.index)
    out = cb.class_b_placebo(rc, rs, w=0.10, n_nulls=200, block=20,
                             rng=np.random.default_rng(77))
    assert 0.05 <= out["real_percentile"] <= 0.95
    assert out["right_tail_p95_pass"] is False


def test_placebo_reports_dann_side_and_never_upgrades():
    rc = seeded_champion(800, seed=5)
    rs = pd.Series(np.random.default_rng(6).normal(0.0008, 0.009, 800), index=rc.index)
    out = cb.class_b_placebo(rc, rs, w=0.10, n_nulls=60, block=20,
                             rng=np.random.default_rng(8))
    for k in ["real_dann", "null_dann_p50", "real_ann_percentile",
              "null_dsr_p50", "null_dsr_p95", "right_tail_p95_pass"]:
        assert k in out
    # instrument output is a necessary-condition verdict, never an adoption claim
    assert out["verdict"] in {"SURVIVES_PLACEBO", "PLACEBO_ARTIFACT"}
    assert "not_an_adoption" in out


# --------------------------------------------------- Class-A instrument (8h, unchanged)
def test_gaussian_matched_placebo_reproduces_r3_geometry():
    """VOL2-R3 frac_pos=1.000 geometry: a positive-mean low-corr stream whose blend dSR
    gain is variance-reduction must be reproduced by ~ALL vol+corr-matched Gaussian nulls
    (8h as flown in R3 - unchanged by the V3 proposal)."""
    rng = np.random.default_rng(31)
    rc = seeded_champion(1200, seed=2)
    rs_vals = rng.normal(0.0005, 0.004, len(rc))          # low-vol positive-mean, corr ~0
    rs = pd.Series(rs_vals, index=rc.index)
    out = cb.gaussian_matched_placebo(rc, rs, w=0.15, n_nulls=100,
                                      rng=np.random.default_rng(12))
    assert out["frac_null_dsr_pos"] == 1.0                # matches the R3 A11/COMP50d finding
    assert out["verdict"] == "PLACEBO_ARTIFACT"


def test_circular_shift_placebo_mistimed_draws():
    rc = seeded_champion(800, seed=3)
    rs = pd.Series(np.random.default_rng(4).normal(0.0006, 0.008, 800), index=rc.index)
    out = cb.circular_shift_placebo(rc, rs, w=0.10, n_nulls=100,
                                    rng=np.random.default_rng(9))
    assert 0.0 <= out["reproduced_frac"] <= 1.0
    assert len(out["null_dsr"]) == 100
    assert out["instrument"] == "circular_shift"


# ------------------------------------------------------- classification + routing
def test_classify_boundaries():
    assert cb.classify(0.94) == "A"
    assert cb.classify(0.0219) == "B"      # HOBR
    assert cb.classify(-0.02) == "B"
    assert cb.classify(0.45) == "STRADDLER"
    assert cb.classify(-0.45) == "STRADDLER"
    assert cb.classify(0.60) == "A"
    assert cb.classify(-0.60) == "A"
    with pytest.raises(ValueError):
        cb.classify(1.2)


def test_straddler_runs_both_stricter_reading_wins():
    """A straddler killed by the Class-A instrument must stay killed even if its Class-B
    reading passes (the placebo can never upgrade; stricter wins)."""
    rc = seeded_champion(1000, seed=13)
    # positively-correlated low-vol positive-mean stream: corr ~ +0.45 (straddle band)
    base = np.random.default_rng(14).normal(0.0005, 0.0055, len(rc))
    rs = pd.Series(base + 0.35 * (rc.values - rc.values.mean()), index=rc.index)
    corr = float(pd.concat([rc, rs], axis=1).corr().iloc[0, 1])
    assert 0.40 < corr < 0.60
    out = cb.placebo_verdict(rc, rs, w=0.10, n_nulls=60, block=20,
                             rng=np.random.default_rng(15))
    assert out["class"] == "STRADDLER"
    assert {"class_b", "gaussian_matched"}.issubset(out["instruments_run"])
    assert out["survives_placebo"] is False               # stricter reading wins
    assert out["killed_by"]


def test_class_b_candidate_runs_only_b1():
    rc = seeded_champion(1000, seed=16)
    rs = pd.Series(np.random.default_rng(17).normal(0.0005, 0.008, 1000), index=rc.index)
    out = cb.placebo_verdict(rc, rs, w=0.10, n_nulls=40, block=20,
                             rng=np.random.default_rng(18))
    assert out["class"] == "B"
    assert out["instruments_run"] == ["class_b"]


# ------------------------------------------------------------- B2 corroborator
def test_timing_split_is_diagnostic_only():
    rc = seeded_champion(1000, seed=19)
    rs = pd.Series(np.random.default_rng(20).normal(0.0006, 0.008, 1000), index=rc.index)
    out = cb.timing_split_diagnostic(rc, rs, w=0.10, n_nulls=40, block=20,
                                     rng=np.random.default_rng(21))
    assert out["status"] == "DIAGNOSTIC_ONLY_never_a_gate"
    assert "H1" in out and "H2" in out
    assert "verdict" not in out                           # no verdict can be derived from it


# ------------------------------------------------------------------ fail-closed
def test_fail_closed_on_degenerate_inputs():
    rc = seeded_champion(300, seed=22)
    good = pd.Series(np.random.default_rng(23).normal(0.0, 0.01, 300), index=rc.index)
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good.iloc[:50], n=5, block=20, rng=np.random.default_rng(0))   # too short
    with pytest.raises(ValueError):
        cb.level_matched_nulls(pd.Series(np.zeros(300), index=rc.index), n=5, block=20,
                               rng=np.random.default_rng(0))                                   # zero vol
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good, n=5, block=200, rng=np.random.default_rng(0))             # block too big
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good, n=5, block=1, rng=np.random.default_rng(0))               # block degenerate
    bad = good.copy()
    bad.iloc[10] = np.nan
    with pytest.raises(ValueError):
        cb.level_matched_nulls(bad, n=5, block=20, rng=np.random.default_rng(0))               # NaN interior
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.10, n_nulls=1, block=20, rng=np.random.default_rng(0))  # n_nulls < 2
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good.reindex(good.index[:-5]), w=0.10, n_nulls=10, block=20,
                           rng=np.random.default_rng(0))                                        # missing days
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.0, n_nulls=10, block=20, rng=np.random.default_rng(0))  # w out of range
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.20, n_nulls=10, block=20, rng=np.random.default_rng(0))  # w > charter cap
