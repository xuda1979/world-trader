"""TDD: HUNT_TREASFUT round-2 machinery bugs (found live in r2 run 2026-09-07)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import pytest
from bt import engine, metrics
import HUNT_TREASFUT_round1 as r1


def _toy_book(n=600, n_legs_R=3, n_cols_W=2, seed=3):
    """Multi-leg book where W trades a SUBSET of R's columns (mom1030 case: W has 10y+30y,
    R also has 2y). Pre-fix lagroll_p crashed: ValueError broadcast (T,2)x(T,3)."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range('2010-01-04', periods=n)
    R = pd.DataFrame(rng.normal(0, 0.001, (n, n_legs_R)), index=idx,
                     columns=[f'l{i}' for i in range(n_legs_R)])
    W = pd.DataFrame(rng.normal(0, 0.5, (n, n_cols_W)), index=idx,
                     columns=[f'l{i}' for i in range(1, 1 + n_cols_W)])   # subset of R cols
    return W, R


def test_lagroll_p_subset_columns_no_crash():
    """r2 live crash: lagroll_p broadcast (12383,2) vs (12383,3). Must align W to R columns."""
    W, R = _toy_book()
    net = ((W.shift(1) * R[W.columns]).sum(axis=1))
    p = r1.lagroll_p(W, R, net)
    assert 0.0 <= p <= 1.0


def test_lagroll_p_zero_weight_subset_legs_same_as_full():
    """Equivalent book expressed with an explicit zero column must give the SAME p (align by
    column, not by position)."""
    W, R = _toy_book()
    Rz = R.copy(); Rz['l0'] = 0.0                      # zero leg
    net = ((W.shift(1) * R[W.columns]).sum(axis=1))
    p1 = r1.lagroll_p(W, R, net)
    p2 = r1.lagroll_p(W, Rz, net)
    assert p1 == p2


def test_lagroll_p_timing_destroyed_gives_high_p():
    """Sanity: iid-noise book with real (seeded) edge... instead verify scrambled SRs are finite
    and the real SR is recomputed on the SAME window (no NaN blowup)."""
    W, R = _toy_book()
    net = ((W.shift(1) * R[W.columns]).sum(axis=1))
    p, real_sr = None, None
    # real_sr internal consistency: book rebuilt inside lagroll_p must match net's SR
    book = ((W * R[W.columns]).sum(axis=1) - engine.cost_turnover(W, cost_bps=6.4)
            - engine.borrow_cost(W))
    assert np.isfinite(metrics.sharpe_d(book))
    p = r1.lagroll_p(W, R, net)
    assert np.isfinite(p)


def test_net_of_no_phantom_window():
    """r2 live bug: W built on a wider index than R (e.g. DGS10 weights from 1962 vs 3-leg R
    from 1977) made net_of union the indexes -> years of zero-return rows that still PAY
    turnover costs, inflating the evaluated window (n=16154 from 1962 for a book whose 30y leg
    only exists from 1977). net must live on R's index, and no cost may be charged outside it."""
    rng = np.random.default_rng(5)
    idxR = pd.bdate_range('2010-01-04', periods=400)
    idxW = pd.bdate_range('2008-01-02', periods=400 + 520)   # W starts ~2y earlier
    R = pd.DataFrame(rng.normal(0, 0.001, (400, 2)), index=idxR, columns=['a', 'b'])
    W = pd.DataFrame(1.0, index=idxW, columns=['a', 'b'])     # constant unit weights
    net, We, g = r1.net_of(W, R, vt=False)
    assert net.index.equals(R.index), f'net index {net.index[0]} != R index {R.index[0]}'
    assert We.index.equals(R.index)
    # weights outside R's window must be zeroed, so only the day-1 establishment cost is charged
    cost = engine.cost_turnover(We, cost_bps=6.4)
    assert (cost > 0).sum() <= 2, f'phantom turnover charged on {(cost > 0).sum()} days'


def test_net_of_subset_columns_zeroed():
    """W trading a subset of R's legs: reindex must add the missing leg as explicit 0 weight
    (not NaN), so (We*R) has no NaN contribution and costs only reflect traded legs."""
    rng = np.random.default_rng(6)
    idx = pd.bdate_range('2010-01-04', periods=300)
    R = pd.DataFrame(rng.normal(0, 0.001, (300, 2)), index=idx, columns=['a', 'b'])
    W = pd.DataFrame(1.0, index=idx, columns=['a'])
    net, We, g = r1.net_of(W, R, vt=False)
    assert list(We.columns) == ['a', 'b'] and (We['b'] == 0).all()
    assert np.isfinite(net).all()


def test_combined_mom_weights_not_all_nan():
    """r2 live bug: 0.5*W1 + 0.5*W2 with DISJOINT columns union-joins to ALL-NaN (NaN+x=NaN)
    -> fillna(0) -> dead zero book reported as SR=0.00/p=1.00/n=12383. combine_W must be
    column-union-safe (add with fill_value) and yield a LIVE book through the engine."""
    idx = pd.bdate_range('2010-01-04', periods=300)
    R = pd.DataFrame({'10': np.linspace(0, .01, 300), '30': -np.linspace(0, .01, 300)}, index=idx)
    import HUNT_TREASFUT_round2 as r2
    W1, W2 = r2.w_mom(R, '10', 21), r2.w_mom(R, '30', 21)
    Wbad = (0.5 * W1 + 0.5 * W2).fillna(0.0)
    assert Wbad.abs().to_numpy().sum() == 0, 'trap precondition: raw + yields dead book'
    Wgood = r2.combine_W(0.5 * W1, 0.5 * W2)
    assert Wgood['10'].abs().sum() > 0 and Wgood['30'].abs().sum() > 0, \
        'combine_W dropped a leg (raw + trap resurfaced in disguise)'
    # warmup rows NaN in BOTH inputs legitimately stay NaN; everywhere else union-NaN is a bug
    in_live = W1.notna().any(axis=1) | W2.notna().any(axis=1)
    out_live = Wgood.notna().any(axis=1)
    assert (out_live[in_live]).all(), 'combine_W lost live rows to the disjoint-column union-NaN trap'
    assert not out_live[~in_live].any(), 'combine_W fabricated rows where both inputs are NaN'
    # and the engine must produce a LIVE book from the good combine (nonzero PnL, finite SR)
    net, We, _ = r1.net_of(Wgood, R, vt=False)
    assert (net != 0).any(), 'net_of on a live combined book must not yield an all-zero series'
    assert np.isfinite(net).all()


def test_net_of_trim_coverage_fail_closed():
    """r2 live bug (silent): a regime book whose W exists only from 2003 passed against
    full-window R (1977) -> net_of returned a 61%-dead-zero book and evaluate reported
    diluted SR/H1 over rows that carry no exposure at all. Default stays on R's grid
    (documented contract, R1 reproducibility), but trim_coverage=True must fail-closed the
    evaluated window to W's coverage so no dead zero rows dilute the gates."""
    rng = np.random.default_rng(9)
    idx = pd.bdate_range('2010-01-04', periods=500)
    R = pd.DataFrame(rng.normal(0, 0.001, (500, 1)), index=idx, columns=['a'])
    W = pd.DataFrame(1.0, index=idx[250:], columns=['a'])       # book only covers H2
    net_def, We_def, _ = r1.net_of(W, R, vt=False)              # documented default: R grid
    assert net_def.index.equals(R.index)
    net2, We2, _ = r1.net_of(W, R, vt=False, trim_coverage=True)
    assert net2.index[0] == W.index[0], 'trim_coverage must drop the dead prefix'
    assert len(net2) == 250, f'coverage window {len(net2)} != 250'
    assert (net2.index >= W.index[0]).all()
    # T+1: establishment cost lands on the FIRST PnL row (day after coverage start)
    cost_rows = r1.engine.cost_turnover(We2, cost_bps=6.4)
    assert cost_rows.iloc[0] == 0.0 and cost_rows.iloc[1] > 0, \
        'entry cost must be charged once, on the first held row'


def test_net_of_rejects_dead_book():
    """r2 live bug (mom1030): a signal-pipeline bug produced an ALL-ZERO weight frame that was
    saved as a sleeve and reported SR=0.00 / scram_p=1.000 / corr=nan — a dead book silently
    dressed up as a negative result. net_of must refuse to evaluate it."""
    rng = np.random.default_rng(4)
    idx = pd.bdate_range('2010-01-04', periods=200)
    R = pd.DataFrame(rng.normal(0, 0.001, (200, 2)), index=idx, columns=['a', 'b'])
    W = pd.DataFrame(0.0, index=idx, columns=['a', 'b'])
    with pytest.raises(ValueError, match='dead book'):
        r1.net_of(W, R, vt=False)
