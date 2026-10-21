"""TDD for HUNT_TIMESFM R6 fraud-catch harness (my OWN engine, not importing targets' libs).

Pins arithmetic that the reproduction depends on:
  1. my sharpe/halves/neg-years match bt.metrics on random data (cross-impl agreement)
  2. T+1: position set at close(t) earns t->t+1 (weights shifted before P&L)
  3. cost: 6.4bps x full |dW|, entry day charged (0 -> w0 counts)
  4. borrow: 0.5%/yr x short notional (prior day)
  5. VT: trailing-only EWMA (shift(1)), clip 3.0, warmup scale=0
  6. scramble: row-permutation of FINAL effective weights, re-costed, p = P(SR_scr >= real)
"""
import sys, os
import numpy as np
import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'work_r6'))
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')

import fraudcatch_r6 as F  # noqa: E402
from bt import metrics as M  # noqa: E402


def test_metrics_agree_with_bt():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 1500), index=pd.bdate_range('2010-01-04', periods=1500))
    assert abs(F.sr(r) - M.sharpe_d(r)) < 1e-12
    h1m, h2m = M.half_split(r)
    h1, h2 = F.halves(r)
    assert abs(h1 - h1m) < 1e-12 and abs(h2 - h2m) < 1e-12
    neg, worst = F.neg_years(r)
    negm, worstm = M.neg_years(r)
    assert neg == negm and abs(worst - worstm) < 1e-12


def test_t1_no_lookahead():
    # a signal that is +1 exactly on days the market went UP must NOT earn on day t
    idx = pd.bdate_range('2010-01-04', periods=6)
    px = pd.Series([100, 101, 100, 103, 102, 104.], index=idx)
    ret = px.pct_change().fillna(0.0)
    w = pd.Series((ret > 0).astype(float), index=idx)  # same-day sign (would leak)
    net, we = F.net_book(w.to_frame('a'), ret.to_frame('a'))
    # effective weights = w.shift(1): day t's P&L uses w_{t-1}. If leaked, SR would be huge.
    assert abs(we['a'].iloc[0]) == 0.0  # day 0 flat (entry on day 1)
    assert abs(we['a'].iloc[1] - w.iloc[0]) < 1e-15


def test_cost_entry_and_full_dw():
    idx = pd.bdate_range('2010-01-04', periods=3)
    w = pd.Series([0.0, 1.0, 1.0], index=idx)
    ret = pd.Series([0.0, 0.01, 0.02], index=idx)
    net, we = F.net_book(w.to_frame('a'), ret.to_frame('a'))
    C = 6.4e-4
    # we = w.shift(1) = [0,0,1]; pnl = we*ret = [0,0,0.02]; cost = |dwe| = [0,0,1]*C
    assert abs(net.iloc[0]) < 1e-15
    assert abs(net.iloc[1]) < 1e-15
    assert abs(net.iloc[2] - (0.02 - C)) < 1e-12


def test_borrow_on_shorts():
    idx = pd.bdate_range('2010-01-04', periods=3)
    w = pd.Series([-1.0, -1.0, 0.0], index=idx)
    ret = pd.Series([0.0, 0.0, 0.0], index=idx)
    net, we = F.net_book(w.to_frame('a'), ret.to_frame('a'))
    B = 0.005 / 252
    C = 6.4e-4
    # my convention: borrow on CURRENT effective short notional
    # (== lib_hunt's short_notional.shift(1) of the RAW pos). Same thing.
    # day1: entry trade into -1.0 charges 1.0*C, borrow B on effective -1 -> net = -C - B
    assert abs(net.iloc[1] - (-C - B)) < 1e-15
    assert abs(net.iloc[2] - (-B)) < 1e-15  # day2: no turnover, borrow on still-short


def test_vt_trailing_only():
    # scale at t must not change if the FUTURE return is altered
    idx = pd.bdate_range('2010-01-04', periods=260)
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0, 0.01, 260), index=idx)
    s1 = F.vt_scale_ewm(r)
    r2 = r.copy(); r2.iloc[-1] *= 50
    s2 = F.vt_scale_ewm(r2)
    pd.testing.assert_series_equal(s1.iloc[:200], s2.iloc[:200])


def test_vt_warmup_zero():
    idx = pd.bdate_range('2010-01-04', periods=30)
    r = pd.Series(0.01, index=idx)
    s = F.vt_scale_ewm(r)
    assert (s.iloc[:19] == 0.0).all()  # min_periods 20 warmup -> scale 0 (flat book)


def test_scramble_p_extremes():
    # smooth (low-turnover) weights aligned with a persistent return edge: real SR high,
    # any circular shift of positions destroys the alignment -> p small
    idx = pd.bdate_range('2010-01-04', periods=800)
    w = pd.Series(np.sin(np.arange(800) / 40.0), index=idx)     # smooth, persistent
    rng = np.random.default_rng(3)
    ret = pd.Series(rng.normal(0.0, 0.01, 800), index=idx) + 0.015 * w.shift(1).fillna(0.0)
    px = 100.0 * (1 + ret).cumprod()                            # engine takes PRICES
    p = F.scramble_p(w, px, n=100, seed=7)
    assert F.sr(F.net_book_cot2(w, px)[0]) > 0.8                # real edge is real
    assert p < 0.10


def test_wide_book_matches_sum_of_legs():
    # multi-leg book: net = sum(we*r) - costs on summed weights; verify vs manual
    idx = pd.bdate_range('2010-01-04', periods=5)
    W = pd.DataFrame({'a': [0, 1, 1, -1, 0.], 'b': [1, 1, 0, 0, -1.]}, index=idx)
    R = pd.DataFrame({'a': [.01, -.01, .005, .002, .001], 'b': [.002, .003, -.001, 0., .004]}, index=idx)
    net, we = F.net_book(W, R)
    we_m = W.shift(1).fillna(0.0)
    pnl = (we_m * R).sum(axis=1)
    to = we_m.diff().abs().sum(axis=1)
    to.iloc[0] = we_m.iloc[0].abs().sum()
    bor = (-we_m.clip(upper=0)).abs().sum(axis=1) * 0.005 / 252
    pd.testing.assert_series_equal(net, (pnl - to * 6.4e-4 - bor).rename('net'),
                                   check_names=False)


# ------------------------------------------------------------------ R6 additions
# (spec tests for the fraud-catch rebuilds — written BEFORE the implementations)


def test_my_expanding_vt_matches_bt_engine():
    # my own expanding-VT implementation must agree with the shared bt engine spec:
    # scale_t = clip(0.10 / (expanding_std(r[:t-1])*sqrt(252)), 0.2, 3.0), min_periods 60
    rng = np.random.default_rng(11)
    idx = pd.bdate_range('2012-01-03', periods=400)
    g = pd.Series(rng.normal(0.0002, 0.008, 400), index=idx)
    mine = F.vt_scale_expanding(g.to_frame('g'))['g']
    from bt import engine as E
    theirs = E.vol_target_scale(g.to_frame('g'))['g']
    pd.testing.assert_series_equal(mine, theirs, check_names=False)


def test_cot2_map_report_to_session_t1():
    # report_date -> panel release_date -> FIRST SESSION STRICTLY AFTER release (T+1);
    # ffill forward; 0.0 before the first release; later report wins on collision.
    px_idx = pd.bdate_range('2020-01-01', periods=30)
    px = pd.Series(100.0, index=px_idx)
    rel = pd.Series(pd.to_datetime(['2020-01-06', '2020-01-13', '2020-01-13']),
                    index=pd.to_datetime(['2020-01-02', '2020-01-09', '2020-01-10']))
    sig = pd.Series([1.0, 0.0, 1.0], index=rel.index)
    daily = F.map_release_to_daily(sig, rel, px)
    assert daily.loc[:'2020-01-06'].eq(0.0).all()          # nothing before first release
    first_session = px_idx[px_idx > pd.Timestamp('2020-01-06')][0]
    assert daily.loc[first_session] == 1.0                 # T+1 entry
    # collision (2020-01-13 release for both 01-09 and 01-10 reports): LATEST report wins
    coll_session = px_idx[px_idx > pd.Timestamp('2020-01-13')][0]
    assert daily.loc[coll_session] == 1.0


def test_cot2_pit_z_segmented_at_break():
    # expanding z (min_periods 26, ddof=0) on report_date; a break date must segment the
    # computation: post-break z must NOT depend on any pre-break row.
    rng = np.random.default_rng(5)
    dates = pd.bdate_range('2018-01-01', periods=120)
    cnt = pd.Series(rng.integers(20, 80, 120).astype(float), index=dates)
    brk = dates[60]
    z_seg = F.pit_expanding_z(cnt, breaks=[brk])
    # recompute post-break segment alone from raw counts
    post = cnt[cnt.index >= brk]
    mu = post.expanding(min_periods=26).mean()
    sd = post.expanding(min_periods=26).std(ddof=0)
    z_ref = (post - mu) / sd.where(sd > 0)
    pd.testing.assert_series_equal(z_seg[post.index], z_ref, check_names=False)
    assert z_seg.dropna().index.min() >= dates[25]         # min_periods warmup honored


def test_rebuild_mom252_lf_matches_published_start():
    # structural: my MOM_252_LF rebuild must be live no earlier than the published book's
    # first date (warmup 252d on NKY starting 1949-05-16 -> published start 1950-12-15)
    net, we = F.rebuild_intl('MOM_252_LF')
    pub = pd.read_csv('/Users/daxu/software/world-trader/campaign/agents/chief/coord/'
                      'HUNT_INTERNATIONAL2/sleeves/INTL_R5_MOM_252_LF.csv',
                      index_col=0, parse_dates=True).iloc[:, 0]
    assert net.index.min() >= pub.index.min()
    assert abs(net.index.min() - pub.index.min()) <= pd.Timedelta(days=10)
    assert len(net) > 18000
