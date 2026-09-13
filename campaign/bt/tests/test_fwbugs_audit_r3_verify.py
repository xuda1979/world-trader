"""AUDIT_FWBUGS R3 verify-only fixtures (charter (c) adjudication) + M22 closure pins.

Charter R3 UPDATE ruled test_beats_passive.py (shipped 21/21 GREEN by HUNT_INTERNATIONAL2)
VERIFY-ONLY: this file adds INDEPENDENT RED-capable fixtures against the shipped
implementation. They pass on the shipped code; any future regression that flips one of
these assertions is a real defect caught here, in a file this agent owns (the shared test
files are concurrently edited by fleet cron agents — write-race observed 2026-09-07 16:30).

M22 (R2's only VACUOUS-EVERYWHERE mutant): the mutant `eq[r.isna()] = np.nan` is an
EQUIVALENT MUTANT — proven exhaustively in
campaign/agents/chief/coord/AUDIT_FWBUGS/work/r3/m22_maxdd_nanpoison.py (180/180 identical;
M22b dropna-compress and M22c output-poison are equivalent too; only the M22d
any-NaN->0.0 fail-open class is distinguishable, 164/180). These pins therefore lock the
max_dd NaN CONTRACT (holes are flat days, all-NaN fails closed, no perfect-drawdown lie)
rather than pretend to kill an unkillable mutation.
"""
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

from bt.metrics import max_dd  # noqa: E402
from bt.beats_passive import (  # noqa: E402
    _as_ret_series, evaluate, spy_buyhold, sixty_forty)

IDX = pd.date_range("2020-01-01", periods=500, freq="B")


# ---------------------------------------------------------------- max_dd / M22 contract

def test_max_dd_nan_hole_is_a_flat_day_answer_unchanged():
    """A NaN day must not change max_dd vs. the same series with the hole filled 0.0
    (pandas skipna carries equity flat through the hole). Kills any future rewrite that
    drops rows (changes the drawdown path length/shape) or poisons the answer."""
    rng = np.random.default_rng(2)
    r = pd.Series(rng.normal(0, 0.01, 300), index=IDX[:300])
    holed = r.copy()
    holed.iloc[[40, 41, 150]] = np.nan
    filled = holed.fillna(0.0)
    assert max_dd(holed) == pytest.approx(max_dd(filled), abs=1e-12)


def test_max_dd_all_nan_fails_closed_nan():
    """All-NaN window is unmeasurable -> NaN, never 0.0 ('perfect drawdown' lie, the
    distinguishable M22d fail-open class) and never a crash."""
    r = pd.Series(np.nan, index=IDX[:100])
    assert np.isnan(max_dd(r))


def test_max_dd_poisoned_window_not_zero():
    """M22d killer: a real drawdown in a window that ALSO has NaN holes must still report
    the (negative) drawdown — any-NaN -> 0.0 returns 164/180 wrong answers on this class."""
    r = pd.Series([0.01, np.nan, 0.02, -0.10, 0.03, np.nan, -0.05], index=IDX[:7])
    d = max_dd(r)
    assert np.isfinite(d) and d < 0, f"NaN-holed drawdown lost: {d}"


# ------------------------------------------------- beats_passive seams (verify-only)

def test_sub_1e3_price_levels_are_returns_by_convention_and_fail_conservative():
    """_as_ret_series' documented convention: values not all >1e3 pass through as returns.
    IEF-realistic levels (~92) are therefore 'returns' ~92/day -> benchmark SR inflates
    enormously -> candidate FAILS. The failure direction must stay CONSERVATIVE (a good
    candidate can be rejected with a confusing verdict; a bad one can NEVER pass)."""
    rng = np.random.default_rng(11)
    ief_px = pd.Series(92 * np.exp(np.cumsum(rng.normal(0.0001, 0.003, 500))), index=IDX)
    r = _as_ret_series(ief_px)
    assert float(r.mean()) > 1.0, "convention changed: sub-1e3 levels now differenced?"
    cand = pd.Series(rng.normal(0.0008, 0.01, 500), index=IDX)  # genuinely decent sleeve
    ev = evaluate(cand, spy=None, ief=ief_px)
    # ief alone constructs no benchmark (needs spy for both spy_bh and sixty_forty)
    assert ev["pass"] is False and ev["reason"] in ("no_benchmark", "no_overlap")
    # WITH spy supplied too, the misread ief must still not let a weak candidate pass
    spy = pd.Series(rng.normal(0.0005, 0.01, 500), index=IDX)
    weak = pd.Series(rng.normal(0.0002, 0.02, 500), index=IDX)  # SR ~0.16, must fail
    ev2 = evaluate(weak, spy=spy, ief=ief_px)
    assert ev2["pass"] is False, "garbage benchmark let a weak sleeve pass (fail-OPEN!)"


def test_spy_buyhold_does_not_mutate_the_callers_series():
    """spy_buyhold copies the input buffer before writing the day-0 flat / entry cost;
    the caller's Series must come back byte-identical."""
    spy = pd.Series([0.01, -0.02, 0.03, 0.04], index=pd.date_range("2020-01-01", periods=4))
    before = spy.copy(deep=True)
    spy_buyhold(spy, spy.index)
    pd.testing.assert_series_equal(spy, before)


def test_sixty_forty_ruin_guard_weights_zero_not_nan():
    """Total ruin (d<=0 in the drift update) must zero the weights — the book goes flat
    from the next day, never NaN. Measured contract: ruin day earns the full -1.0 gross
    minus the day-1 entry cost (-1.00064); the NEXT day carries the one-time 6.4bps
    LIQUIDATION cost of the zeroed 1.0 notional (-0.00064); every day after is exactly
    flat 0.0. A SINGLE-leg wipe instead concentrates wealth in the surviving leg
    (verified: 0.6/0.4 through spy -100% leaves the IEF leg earning its 0.001)."""
    spy = pd.Series([0.02, -1.0, 0.01, 0.01], index=pd.date_range("2020-01-01", periods=4))
    ief = pd.Series([0.001, -1.0, 0.001, 0.001], index=pd.date_range("2020-01-01", periods=4))
    s = sixty_forty(spy, ief, spy.index)
    assert np.isfinite(s.to_numpy()).all()
    assert float(s.iloc[1]) == pytest.approx(-1.0 - 6.4e-4)   # ruin day, full -1 + entry cost
    assert float(s.iloc[2]) == pytest.approx(-6.4e-4)         # liquidation cost, zero weights
    assert float(s.iloc[3]) == 0.0                            # flat forever after
    # single-leg wipe: finite throughout, surviving leg keeps earning
    ief2 = pd.Series([0.001] * 4, index=pd.date_range("2020-01-01", periods=4))
    s2 = sixty_forty(spy, ief2, spy.index)
    assert np.isfinite(s2.to_numpy()).all()
    assert float(s2.iloc[-1]) == pytest.approx(0.001)


def test_evaluate_candidate_with_nan_holes_judged_on_observations():
    """A candidate with NaN days (real-world sleeves) is judged on its COMPRESSED finite
    observations (dropna semantics, same as the whole bt.metrics layer), and the verdict
    stays fail-closed-consistent: candidate SR computed here from the same compression must
    reproduce the gate's number exactly."""
    rng = np.random.default_rng(5)
    spy = pd.Series(rng.normal(0.0005, 0.01, 800),
                    index=pd.date_range("2019-06-01", periods=800, freq="B"))
    cand = pd.Series(rng.normal(0.0006, 0.008, 500), index=IDX)
    cand.iloc[100:150] = np.nan
    ev = evaluate(cand, spy=spy)
    from bt.metrics import sharpe_d
    assert ev["candidate_sr"] == pytest.approx(sharpe_d(cand.dropna()), rel=1e-12)
    assert ev["pass"] is True          # strong sleeve still passes vs real SPY B&H
