"""HUNT_MACRO2 round-1 TDD: no-lookahead + PIT release-lag properties.

These run BEFORE the sleeve evaluation script in the pipeline of trust:
 1. PIT alignment: a monthly macro value for reference month m must NOT be available
    on any date strictly before month_end(m) + pub_days.
 2. No-lookahead probe: weights rebuilt from data truncated at date T equal the
    full-sample weight path's prefix up to T.
 3. T+1: the evaluated weight path used for PnL on day t equals the signal weights at t-1.
Run: pytest campaign/agents/chief/coord/HUNT_MACRO2/tests/ -q
"""
import sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_MACRO2/work_r1")
macro = pytest.importorskip("HUNT_MACRO2_round1")


# ---------------------------------------------------------------- 1. PIT alignment
def test_monthly_value_not_available_before_release():
    """INDPRO for month m (pub_days=45) must be invisible until m_end+45d."""
    s = pd.Series([100.0, 110.0, 120.0],
                  index=pd.to_datetime(['2020-01-31', '2020-02-29', '2020-03-31']))
    pit = macro.pit_monthly(s, pub_days=45)
    cal = pd.bdate_range('2020-01-01', '2020-05-31')
    pit_d = pit.reindex(cal).ffill()
    # 2020-01 value (avail 2020-03-16) must not show on 2020-03-13
    assert np.isnan(pit_d.loc['2020-03-13'])
    # ... and must show from 2020-03-16 onward (next bday 2020-03-16 is a Monday)
    assert pit_d.loc['2020-03-16':].first_valid_index() is not None
    first = pit_d.first_valid_index()
    assert first >= pd.Timestamp('2020-01-31') + pd.Timedelta(days=45)
    assert pit_d.dropna().iloc[0] == 100.0


def test_daily_pit_shift():
    """Daily series with pub_days=k: on any date d the visible value is the one printed at
    the latest print date p with p+k (rolled to next bday) <= d — never a later print."""
    idx = pd.bdate_range('2020-01-01', periods=10)
    s = pd.Series(np.arange(10.0), index=idx)
    pit = macro.pit_daily(s, pub_days=2)
    stamps = (idx + pd.Timedelta(days=2))
    for d, v in pit.items():
        # latest print whose stamp lands on/before d after weekend roll to NEXT bday
        rolled = [t if t.weekday() < 5 else t + pd.offsets.BDay(1) for t in stamps]
        elig = [i for i, t in enumerate(rolled) if t <= d]
        assert elig, f'no eligible print for {d}'
        assert v == s.iloc[elig[-1]], f'{d}: visible {v} != print[{elig[-1]}] {s.iloc[elig[-1]]}'
    # visibility lag is at least pub_days calendar days
    first_visible = pit.index[0]
    assert (first_visible - idx[0]).days >= 2


# ---------------------------------------------------------------- 2. no-lookahead
def test_no_lookahead_credit_composite():
    """Truncating all inputs at T (DATE-based) and rebuilding weights == full-sample prefix."""
    T = pd.Timestamp('2016-06-30')
    parts_full = macro.credit_parts(('dbaa', 'nfci'), N=126)
    W_full = macro.w_credit(parts=parts_full)
    parts_tr = {k: v[v.index <= T] for k, v in parts_full.items()}
    W_tr = macro.w_credit_from_parts(parts_tr)
    exp = W_full[W_full.index <= T]
    pd.testing.assert_frame_equal(exp.round(10), W_tr.reindex(exp.index).round(10))


def test_no_lookahead_activity_composite():
    T = pd.Timestamp('2016-06-30')
    act_full, parts_full = macro.w_activity()
    parts_tr = {k: v[v.index <= T] for k, v in parts_full.items()}
    act_tr, _ = macro.w_activity(parts=parts_tr)
    exp = act_full[act_full.index <= T]
    np.testing.assert_allclose(exp.values, act_tr.reindex(exp.index).values, atol=1e-10)


# ---------------------------------------------------------------- 3. T+1 mechanics
def test_net_of_is_t_plus_1():
    """PnL at t must use weights dated t-1 (no same-day leak)."""
    rng = np.random.default_rng(3)
    idx = pd.bdate_range('2010-01-01', periods=500)
    W = pd.DataFrame({'x': pd.Series(rng.standard_normal(500).round(2), index=idx)})
    R = pd.DataFrame({'x': pd.Series(rng.standard_normal(500) / 100, index=idx)})
    net, We, _ = macro.net_of(W, R, vt=False)
    gross_manual = (We * R).sum(axis=1)
    # on days where the signal CHANGED at t-1 -> t, We reflects the OLD signal at t
    assert np.allclose(We.values, W.shift(1).fillna(0.0).values)


def test_cost_full_dw_day1_seeded():
    """Day-1 entry notional must be charged (prev seeded with zeros). Weight established at
    close of day0 is HELD into day1 (T+1), so the entry cost lands on day1's PnL row."""
    idx = pd.bdate_range('2010-01-01', periods=5)
    W = pd.DataFrame({'x': [1.0] * 5}, index=idx)
    R = pd.DataFrame({'x': [0.0] * 5}, index=idx)
    net, We, _ = macro.net_of(W, R, vt=False)
    day1_cost = 1.0 * 6.4 / 1e4
    assert abs(-net.iloc[1] - day1_cost) < 1e-12   # entry charged on first held day
    assert abs(net.iloc[0]) < 1e-12                # day0 earns nothing (signal not yet traded)


def test_net_of_column_name_mismatch():
    """REGRESSION (r1): DataFrame*DataFrame aligns on COLUMNS — a W named 'sig' vs R named
    'qqq' produced all-NaN gross = pure cost churn (every sleeve read SR -4 with 0 vol).
    net_of must pair positionally: net == We*R - cost - borrow regardless of column names."""
    rng = np.random.default_rng(11)
    idx = pd.bdate_range('2015-01-01', periods=400)
    w = pd.Series(np.sign(rng.standard_normal(400)), index=idx)
    r = pd.Series(rng.standard_normal(400) / 100, index=idx)
    net, We, gross = macro.net_of(w.to_frame('sig'), r.to_frame('qqq'), vt=False)
    # the pre-fix bug: gross was identically 0 (all-NaN product) -> net was pure cost
    assert gross.abs().sum() > 0, 'gross is zero: W/R were not paired positionally'
    # random +/-1 weights flip -> real turnover cost; borrow on short legs; margin 0 (lev=1)
    exp = (We['sig'] * r) - bg_engine_cost(We) - macro.engine.borrow_cost(We)
    got = net.reindex(exp.index)
    pd.testing.assert_series_equal(got.iloc[2:], exp.iloc[2:], check_names=False)


def bg_engine_cost(We):
    from bt.engine import cost_turnover
    return cost_turnover(We, cost_bps=6.4)


def test_net_of_multi_leg_column_order():
    """Multi-leg books must pair W columns with R columns BY NAME (order-independent)."""
    idx = pd.bdate_range('2015-01-01', periods=50)
    W = pd.DataFrame({'a': 1.0, 'b': -1.0}, index=idx)
    R = pd.DataFrame({'b': 0.01, 'a': 0.02}, index=idx)   # deliberately reversed order
    net, We, _ = macro.net_of(W, R, vt=False)
    # held book (by-name pairing despite reversed R column order):
    #   gross = +1*0.02 + (-1)*0.01 = 0.01/day
    #   borrow = |short 1.0| * 0.005/252 = 1.984127e-05, margin = (gross 2.0 - 1) * 0.045/252
    borrow = 1.0 * 0.005 / 252.0
    margin = 1.0 * 0.045 / 252.0
    exp = 0.01 - borrow - margin
    assert abs(net.iloc[10:].mean() - exp) < 1e-12
