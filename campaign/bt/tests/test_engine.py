"""TDD tests for bt.engine — the core honest-backtest properties."""
import numpy as np, pandas as pd
from bt import engine as E


def _panel(n=300):
    rng = np.random.default_rng(7)
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    r = pd.DataFrame(rng.normal(0.0005, 0.01, size=(n, 3)), index=idx,
                     columns=['a', 'b', 'c'])
    return r


def test_lag_signal_no_same_day():
    idx = pd.date_range('2020-01-01', periods=5, freq='B')
    sig = pd.Series(1.0, index=idx)
    pos = E.lag_signal(sig)
    # position today uses yesterday's signal (first day has no prior signal)
    assert np.isnan(pos.iloc[0]) or pos.iloc[0] == 0.0
    assert pos.iloc[1] == sig.iloc[0]
    assert pos.iloc[-1] == sig.iloc[-2]


def test_vol_target_no_lookahead():
    r = _panel()
    r2 = r.copy(); r2.iloc[100, 0] = r2.iloc[100, 0] * 10
    s1 = E.vol_target_scale(r)
    s2 = E.vol_target_scale(r2)
    # scale at row t must use returns r[0..t-1] only (no same-day leak):
    # perturbing r[100] must NOT change scale at row 100 (uses r[0..99]),
    # but MAY change scale at row 101 (which uses r[0..100], known at close 100).
    assert np.allclose(s1.iloc[100].values, s2.iloc[100].values, atol=1e-12)


def test_vol_target_bounds():
    r = _panel()
    s = E.vol_target_scale(r)
    assert s.min().min() >= 0.2 - 1e-12
    assert s.max().max() <= 3.0 + 1e-12


def test_cap_leverage_enforces_bound():
    idx = pd.date_range('2020-01-01', periods=2, freq='B')
    w = pd.DataFrame({'a': [1.0, 2.0], 'b': [1.0, -1.0]}, index=idx)
    wc = E.cap_leverage(w, max_lev=1.6)
    gross = wc.abs().sum(axis=1)
    # day0 gross 2.0 -> capped to 1.6; day1 gross 3.0 -> capped to 1.6
    assert gross.iloc[0] <= 1.6 + 1e-12
    assert gross.iloc[1] <= 1.6 + 1e-12


def test_cap_leverage_identity_below_bound():
    idx = pd.date_range('2020-01-01', periods=2, freq='B')
    w = pd.DataFrame({'a': [0.8, 0.5]}, index=idx)   # gross 0.8, 0.5 < 1.6
    wc = E.cap_leverage(w, max_lev=1.6)
    assert np.allclose(wc.values, w.values)


def test_cost_turnover_one_side():
    idx = pd.date_range('2020-01-01', periods=2, freq='B')
    w = pd.DataFrame({'a': [0.0, 1.0]}, index=idx)
    c = E.cost_turnover(w)
    # ONE-SIDE |dw|=1.0 -> 1.0*6.4e-4 (no 0.5; matches champion reb = |dw|*bps, AUDIT_FRAMEWORK A1)
    assert np.allclose(c.iloc[1], 1.0 * 6.4e-4)


def test_margin_cost_zero_below_one():
    g = pd.Series([0.5, 1.0, 1.6, 2.0])
    m = E.margin_cost(g, rate=0.045, max_lev=1.6)
    # margin only on (gross - 1)+  : gross<=1 -> 0; gross=1.6 -> 0.6; gross=2.0 -> 1.0
    assert m.iloc[0] == 0.0 and m.iloc[1] == 0.0
    assert np.allclose(m.iloc[2], 0.6 * 0.045 / 252.0)
    assert np.allclose(m.iloc[3], 1.0 * 0.045 / 252.0)


def test_borrow_on_shorts():
    idx = pd.date_range('2020-01-01', periods=1)
    w = pd.DataFrame({'a': [1.0], 'b': [-0.5]}, index=idx)
    b = E.borrow_cost(w, borrow_frac=0.005)
    assert np.allclose(b.iloc[0], 0.5 * 0.005 / 252.0)
