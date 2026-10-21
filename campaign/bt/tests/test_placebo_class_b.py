"""HUNT_VOL2 R7 charter (a) — Class-B LEVEL-MATCHED null reference implementation:
behavior pins on a SYNTHETIC fixture only (no production data touched).

V3 PROPOSAL instrument (work_r6/placebo_orthogonal_memo.md §3, Class B / B1) built as a
REUSABLE HELPER in the authoring agent's dir:
  campaign/agents/chief/coord/HUNT_VOL2/work_r7/class_b_placebo.py
— NOT in bt/, and gates.py is UNTOUCHED by this round. Ratification of the V3 contract
change belongs to AUDIT_GATES2; until then this pins the REFERENCE IMPLEMENTATION only:

  * B1: 200 block-bootstrap draws of the candidate's own stream matched on
    mean/vol/skew/autocorr (level-matched = the blend's mean-injection is priced OUT of
    the statistic instead of saturating it); real blend dSR must sit at p95+ of its own
    null to survive.
  * timing-split demoted to diagnostics-only (B2 corroborator; §11 rule).
  * straddlers run BOTH instruments (Class-A §8h as flown + Class-B B1); the stricter
    reading wins; a placebo verdict can never UPGRADE a candidate.

TDD: written RED first (collection failure — class_b_placebo.py did not exist);
GREEN after the helper landed. Validation against the two known published cases
(VOL2-R3 frac_pos=1.000 Class-A geometry; CAMP_COST R6 HOBR Class-B
real dSR p1.00 / real dAnn p0.00) lives in the authoring agent's dir:
  work_r7/test_class_b_placebo.py + work_r7/validate_known_cases.py
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.environ.get("WORLD_TRADER_ROOT", "/Users/daxu/software/world-trader")
HELPER_DIR = os.path.join(
    ROOT, "campaign/agents/chief/coord/HUNT_VOL2/work_r7")
sys.path.insert(0, HELPER_DIR)

try:
    import class_b_placebo as cb  # noqa: E402
except ImportError as _e:  # RED-first contract: fail collection, never skip
    pytest.fail(f"class_b_placebo.py helper missing (RED-first contract): {_e}")


# ------------------------------------------------------------------- fixtures
def _mk(vals, start="2010-01-04"):
    return pd.Series(np.asarray(vals, dtype=float),
                     index=pd.bdate_range(start, periods=len(vals)))


def _crisis_champion(n=1500, seed=7):
    """Synthetic champion with three crisis episodes (skewed-left, mild AC). Drift is
    set well above the episode drag so the book is unambiguously positive-SR for any
    seed (a negative-SR book inverts the dSR sign: variance reduction HURTS it, and the
    timed-vs-null geometry below would flip — that degenerate case is not the pin)."""
    rng = np.random.default_rng(seed)
    r = rng.normal(0.0012, 0.007, n)
    r[400:415] -= 0.012
    r[900:918] -= 0.010
    r[1300:1310] -= 0.011
    return _mk(r)


def _timing_sleeve(rc, seed=42):
    """Candidate with REAL timing content: flat except on champion crisis days."""
    rng = np.random.default_rng(seed)
    v = np.full(len(rc), -0.0002)
    crisis = rc.values < np.percentile(rc.values, 3.0)
    v[crisis] = 0.012 + 0.004 * rng.standard_normal(int(crisis.sum()))
    return pd.Series(v, index=rc.index)


def _coin_sleeve(rc, seed=2024):
    """Pure positive-mean stream, no timing content (the mean-injection control)."""
    return pd.Series(np.random.default_rng(seed).normal(0.0006, 0.008, len(rc)),
                     index=rc.index)


# --------------------------------------------------------------- B1 mechanics
def test_b1_nulls_match_moments_and_break_alignment():
    s = _coin_sleeve(_crisis_champion(1200, seed=3), seed=5)
    m0 = cb.stream_moments(s)
    nulls = cb.level_matched_nulls(s, n=40, block=20, rng=np.random.default_rng(5))
    assert len(nulls) == 40
    for d in nulls:
        md = cb.stream_moments(d)
        assert abs(md["mean"] - m0["mean"]) < 1e-15      # exact: level is NOT the test
        assert abs(md["vol"] - m0["vol"]) < 1e-15        # exact
        assert abs(md["ac1"] - m0["ac1"]) < 0.15         # preserved approximately
        assert abs(md["skew"] - m0["skew"]) < 0.6        # preserved approximately
    # at least one draw genuinely differs from the real stream (not a no-op)
    assert min(float((d.values != s.values).mean()) for d in nulls) > 0.30


def test_b1_timed_candidate_survives_right_tail():
    champ = _crisis_champion()
    out = cb.class_b_placebo(champ, _timing_sleeve(champ, seed=43),
                             w=0.10, n_nulls=200, block=20,
                             rng=np.random.default_rng(123))
    assert out["real_dsr"] > 0
    assert out["real_percentile"] >= 0.95
    assert out["right_tail_p95_pass"] is True


def test_b1_mean_injection_coin_fails_right_tail():
    """The documented failure mode of §8h-as-mistiming, inverted: a positive-mean stream
    with NO timing sits at the CENTER of its own level-matched null — mean-injection is
    priced out instead of saturating the instrument."""
    champ = _crisis_champion(1500, seed=9)
    out = cb.class_b_placebo(champ, _coin_sleeve(champ, seed=2025),
                             w=0.10, n_nulls=200, block=20,
                             rng=np.random.default_rng(77))
    assert 0.05 <= out["real_percentile"] <= 0.95
    assert out["right_tail_p95_pass"] is False


# ------------------------------------------------------- routing / class rules
def test_classify_thresholds():
    assert cb.classify(0.94) == "A"        # correlated overlay (VOL2-R3 family)
    assert cb.classify(0.0219) == "B"      # HOBR corr_champ
    assert cb.classify(-0.02) == "B"
    assert cb.classify(0.45) == "STRADDLER"
    assert cb.classify(-0.45) == "STRADDLER"
    assert cb.classify(0.60) == "A"
    with pytest.raises(ValueError):
        cb.classify(1.2)


def test_class_b_candidate_runs_b1_only():
    rc = _crisis_champion(1000, seed=16)
    rs = _coin_sleeve(rc, seed=17)
    out = cb.placebo_verdict(rc, rs, w=0.10, n_nulls=40, block=20,
                             rng=np.random.default_rng(18))
    assert out["class"] == "B"
    assert out["instruments_run"] == ["class_b"]


def test_straddler_runs_both_stricter_reading_wins():
    rc = _crisis_champion(1000, seed=13)
    base = np.random.default_rng(14).normal(0.0005, 0.0055, len(rc))
    rs = pd.Series(base + 0.35 * (rc.values - rc.values.mean()), index=rc.index)
    corr = float(pd.concat([rc, rs], axis=1).corr().iloc[0, 1])
    assert 0.40 < corr < 0.60
    out = cb.placebo_verdict(rc, rs, w=0.10, n_nulls=60, block=20,
                             rng=np.random.default_rng(15))
    assert out["class"] == "STRADDLER"
    assert {"class_b", "gaussian_matched"}.issubset(out["instruments_run"])
    assert out["survives_placebo"] is False          # placebo can never upgrade
    assert out["killed_by"]


def test_class_a_geometric_artifact_reproduces_r3_result():
    """VOL2-R3 / SECTOR2-R3 A11 geometry (published: frac_null_dsr_pos=1.0,
    corr_champ -0.15): a NEGATIVELY-loaded low-vol positive-mean stream's blend dSR
    gain is reproduced by ALL vol+corr-matched Gaussian nulls => PLACEBO_ARTIFACT.
    The Class-A instrument is UNCHANGED by the V3 proposal (8h as flown). The
    negative loading is the mechanism: vol-matched nulls inherit the champion-
    hedging covariance, so the diversification arithmetic dominates by construction."""
    rc = _crisis_champion(1200, seed=2)
    zc = (rc.values - rc.values.mean()) / rc.values.std()
    zb = np.random.default_rng(32).normal(0, 1, len(rc))
    rs = pd.Series(0.0035 * (-0.15 * zc + np.sqrt(1 - 0.15 ** 2) * zb) + 0.0005,
                   index=rc.index)
    out = cb.gaussian_matched_placebo(rc, rs, w=0.15, n_nulls=100,
                                      rng=np.random.default_rng(12))
    assert out["frac_null_dsr_pos"] == 1.0
    assert out["verdict"] == "PLACEBO_ARTIFACT"


# ------------------------------------------------------------ B2 corroborator
def test_timing_split_is_diagnostic_only():
    rc = _crisis_champion(1000, seed=19)
    rs = _coin_sleeve(rc, seed=20)
    out = cb.timing_split_diagnostic(rc, rs, w=0.10, n_nulls=40, block=20,
                                     rng=np.random.default_rng(21))
    assert out["status"] == "DIAGNOSTIC_ONLY_never_a_gate"
    assert "H1" in out and "H2" in out
    assert "verdict" not in out


# ------------------------------------------------------------------ fail-closed
def test_fail_closed_on_degenerate_inputs():
    rc = _crisis_champion(300, seed=22)
    good = pd.Series(np.random.default_rng(23).normal(0.0, 0.01, 300), index=rc.index)
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good.iloc[:50], n=5, block=20, rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.level_matched_nulls(pd.Series(np.zeros(300), index=rc.index), n=5, block=20,
                               rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good, n=5, block=200, rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.level_matched_nulls(good, n=5, block=1, rng=np.random.default_rng(0))
    bad = good.copy()
    bad.iloc[10] = np.nan
    with pytest.raises(ValueError):
        cb.level_matched_nulls(bad, n=5, block=20, rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.10, n_nulls=1, block=20,
                           rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good.reindex(good.index[:-5]), w=0.10, n_nulls=10,
                           block=20, rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.0, n_nulls=10, block=20,
                           rng=np.random.default_rng(0))
    with pytest.raises(ValueError):
        cb.class_b_placebo(rc, good, w=0.20, n_nulls=10, block=20,
                           rng=np.random.default_rng(0))


# ------------------------------------------------------- no-contract-edit guard
def test_gates_module_untouched_by_this_round():
    """Charter: gates.py UNTOUCHED by VOL2. Pin that no placebo/class-b surface leaked
    into bt/gates.py (the V3 per-class instrument is a PROPOSAL until AUDIT_GATES2
    ratifies it — it must NOT appear as code or a threshold anywhere in gates.py)."""
    gates_path = os.path.join(ROOT, "campaign/bt/gates.py")
    src = open(gates_path, "r").read()
    assert "class_b" not in src and "level_matched" not in src
    assert "placebo" not in src.lower()
