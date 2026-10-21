"""AUDIT_FWBUGS ROUND 2 (a): boundary-condition adversarial tests.

RED-first per charter: single-row frames, empty frames, all-NaN input, duplicate dates,
tz-naive vs tz-aware index, pandas 3.x behavior. Each test targets a suspected silent
fail-open or an unhandled boundary in the R1-landed code.
"""
import os, sys
import numpy as np, pandas as pd
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt import metrics as M, engine as E, reconcile as R


# ---------------- BUG-3 suspect: ann_geo all-NaN returns 0.0 (fail-open) ----------------

def test_ann_geo_all_nan_is_nan_not_zero():
    """BUG SUSPECT: (1+r).prod() on an all-NaN series is 1.0 (pandas skipna), so both ruin
    guards (non-finite, <=0) pass and ann_geo reports 0.0% — a perfect 'no information'
    year books as a flat-zero year. Sibling ann_arith returns NaN. Same fail-open class as
    R1's neg_years bug. Honest: a series with ZERO finite observations must be NaN."""
    r = pd.Series([np.nan] * 252)
    v = M.ann_geo(r)
    assert not (v == 0.0), f"all-NaN ann_geo must not report a clean 0.0 (got {v})"
    assert np.isnan(v), f"all-NaN ann_geo must be NaN (got {v})"


def test_ann_geo_single_nan_is_nan_too():
    r = pd.Series([np.nan])
    assert np.isnan(M.ann_geo(r)), "1-row all-NaN must be NaN, not 0.0"


def test_ann_geo_mixed_nan_still_finite_min_count():
    """The min_count fix must not change mixed-series semantics: >=1 finite obs -> finite."""
    r = pd.Series([np.nan, 0.01, np.nan, -0.005])
    v = M.ann_geo(r)
    assert np.isfinite(v), f"mixed NaN series with finite obs must stay finite, got {v}"


# ---------------- BUG-4 suspect: cost_turnover crashes on empty frame ----------------

def test_cost_turnover_empty_frame_is_empty_not_crash():
    """R1's day-1 zero-seed does prev.iloc[0] = 0.0, which on a 0-row frame raises
    IndexError (iloc cannot enlarge). Gates/audit code must fail-closed on degenerate
    input, not blow up downstream of a sleeve that produced no rows."""
    w = pd.DataFrame(index=pd.DatetimeIndex([]), columns=['a'], dtype=float)
    c = E.cost_turnover(w)
    assert len(c) == 0, "empty weights -> empty cost series"
    assert float(c.sum()) == 0.0


def test_cost_turnover_single_row_charges_entry():
    """Boundary the other way: a 1-row frame IS the establishment trade."""
    w = pd.DataFrame({'a': [0.7]}, index=pd.date_range('2020-01-01', periods=1))
    c = E.cost_turnover(w, cost_bps=6.4)
    assert abs(c.iloc[0] - 0.7 * 6.4 / 1e4) < 1e-15, f"got {c.iloc[0]}"


# ---------------- BUG-5 suspect: turnover_reconciles crashes on empty pos_path ---------

def test_turnover_reconciles_empty_pos_path_fails_closed():
    """Same R1 zero-seed crash class in reconcile.turnover_reconciles: empty pos_path
    raised IndexError instead of returning ok=False."""
    led = pd.DataFrame({'sleeve': ['a'], 'date': [pd.Timestamp('2020-01-01')],
                        'qty_notional': [5.0]})
    pos = pd.DataFrame(index=pd.DatetimeIndex([]), columns=['a'], dtype=float)
    res = R.turnover_reconciles(led, pos)
    assert res['ok'] is False, f"empty pos_path with nonzero ledger must FAIL closed, got {res}"
    assert np.isinf(res['max_rel']), f"max_rel must be inf on the fail-closed path, got {res}"


def test_turnover_reconciles_both_empty_is_ok_zero():
    """Both sides empty: nothing traded, nothing led -> vacuously consistent (ok)."""
    led = pd.DataFrame({'sleeve': pd.Series(dtype=object),
                        'date': pd.Series(dtype='datetime64[ns]'),
                        'qty_notional': pd.Series(dtype=float)})
    pos = pd.DataFrame(index=pd.DatetimeIndex([]), columns=['a'], dtype=float)
    res = R.turnover_reconciles(led, pos)
    assert res['ok'] is True, f"both-empty must reconcile as zero/zero, got {res}"


# ---------------- boundary probes pinned as behavior (no silent flips allowed) ---------

def test_neg_years_duplicate_dates_counted_per_group():
    """Duplicate dates must not crash year grouping (groupby on year key, dup rows sum)."""
    idx = pd.to_datetime(['2020-01-02', '2020-01-02', '2020-01-03', '2020-01-06', '2020-01-07'])
    neg, worst = M.neg_years(pd.Series([-0.5, -0.5, 0.1, 0.1, 0.1], index=idx))
    assert neg == 1 and worst < 0


def test_cap_leverage_single_row_within_cap_untouched():
    w = pd.DataFrame({'a': [0.5]}, index=pd.date_range('2020-01-01', periods=1))
    out = E.cap_leverage(w, max_lev=1.6)
    assert abs(out['a'].iloc[0] - 0.5) < 1e-15, "under-cap row must pass through unchanged"


def test_shortability_gate_single_row_frame():
    from bt.shortability import shortability_gate
    w = pd.DataFrame({'A': [-1.0], 'B': [-0.4]}, index=pd.date_range('2020-01-01', periods=1))
    gated, borrow, dropped = shortability_gate(w, {'B': 'NONE'})
    assert dropped == ['B']
    assert gated['A'].iloc[0] == -1.0 and gated['B'].iloc[0] == 0.0
    assert abs(borrow.iloc[0] - 0.005 / 252.0) < 1e-15


def test_scramble_positions_too_short_for_block_fails_closed():
    """T=40 with block=20: no rollable window -> unmeasurable -> (NaN, real_sr), and
    gates.run must translate that into scr_ok=False, composite pass=False."""
    from bt.gates import scramble_positions, run
    rng = np.random.default_rng(3)
    sig = np.sign(rng.normal(size=40))
    r = pd.Series(rng.normal(0.0005, 0.01, 40),
                  index=pd.date_range('2020-01-01', periods=40, freq='B'))
    p, real = scramble_positions(sig, r.values, block=20)
    assert np.isnan(p) and np.isfinite(real)
    rep = run(r, sig=sig, scramble_n=50)
    assert rep['scr_ok'] is False and rep['pass'] is False


def test_gates_run_tz_aware_index_completes():
    """tz-aware books (non-US calendars) must flow through the whole gate, incl. year
    grouping and monthly halves, without crashing."""
    from bt.gates import run
    idx = pd.date_range('2020-01-01', periods=300, tz='Asia/Tokyo', freq='B')
    rng = np.random.default_rng(11)
    r = pd.Series(rng.normal(0.0008, 0.01, 300), index=idx)
    rep = run(r, ref=None)
    assert set(['sr_ok', 'halves_ok', 'neg_ok', 'scr_ok']).issubset(rep)
    assert rep['neg_years'] >= 0


def test_neg_years_non_datetime_index_raises_clear_error():
    """A non-DatetimeIndex has no .year; demand a clear ValueError naming the problem,
    not a bare AttributeError from inside the groupby."""
    with pytest.raises(ValueError, match="[Dd]atetime"):
        M.neg_years(pd.Series([-0.1, 0.1, 0.1]))


# ---------------- plateau_ok / corr_to boundary pins (charter (a)) ----------------

def test_plateau_nan_neighbor_fails_closed():
    """A NaN neighbor SR is unmeasurable, not good: must not count as >= threshold."""
    from bt.gates import plateau_ok
    ok, info = plateau_ok({1: 2.0, 2: 2.5, 3: float('nan')}, 2)
    assert ok is False and len(info['good_neighbors']) == 1


def test_plateau_exactly_80pct_of_peak_passes():
    """Contract is >= (1-tol)*peak: neighbor at exactly 0.8*peak is ON the plateau."""
    from bt.gates import plateau_ok
    ok, info = plateau_ok({1: 2.0, 2: 2.5, 3: 2.0}, 2)
    assert ok is True and set(info['good_neighbors']) == {1, 3}


def test_plateau_single_key_grid_fails_closed():
    """A 1-point grid has no neighbors to certify a plateau -> fail (never 'trivially ok')."""
    from bt.gates import plateau_ok
    ok, info = plateau_ok({2: 2.5}, 2)
    assert ok is False and info.get('edge') is True


def test_corr_to_constant_ref_is_nan_not_crash():
    from bt.gates import corr_to
    p = pd.date_range('2020-01-01', periods=5)
    v = corr_to(pd.Series(1.0, index=p), pd.Series([1, 2, 3, 4, 5.], index=p))
    assert np.isnan(v)
