"""TDD RED->GREEN tests for RES_CREDIT (charter: campaign/team/charters/RES_CREDIT.md).

V2 §0 convention: gates.run(r=per-unit, sig=effective weight) => sig*r == held gross book.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_CREDIT")

import numpy as np
import pandas as pd
import pytest

import credit_lib as C


def _flat_px(n=120, start=100.0):
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    return pd.Series(start, index=idx)


def test_zscore_invariant_to_future_price():
    """Perturbing day t must not change day-(t-1) z (no future info in decisions)."""
    x = pd.Series(np.linspace(50, 60, 60))
    z1 = C.zscore_trailing(x, win=20)
    x2 = x.copy(); x2.iloc[-1] += 10.0
    z2 = C.zscore_trailing(x2, win=20)
    assert abs(z1.iloc[-2] - z2.iloc[-2]) < 1e-12


def test_net_of_is_t_plus_1():
    """Weights decided at t earn from t+1: day-0 effective weight must be 0."""
    idx = pd.date_range('2020-01-01', periods=30, freq='B')
    W = pd.DataFrame({'a': np.ones(30)}, index=idx)
    R = pd.DataFrame({'a': 0.001}, index=idx)
    net, We, gross = C.net_of(W, R, vt=False)
    assert We['a'].iloc[0] == 0.0
    assert We['a'].iloc[1] == 1.0


def test_net_of_sig_r_equals_gross_book():
    """V2 §0 fixture: We * rpu must equal the held gross book pre-cost (atol 1e-12)."""
    rng = np.random.default_rng(3)
    idx = pd.date_range('2020-01-01', periods=200, freq='B')
    W = pd.DataFrame({'a': rng.choice([-1.0, 0.0, 1.0], 200)}, index=idx)
    R = pd.DataFrame({'a': rng.normal(0, 0.01, 200)}, index=idx)
    net, We, gross = C.net_of(W, R, vt=False)
    held = (We * R.fillna(0.0)).sum(axis=1)
    assert np.allclose((We['a'] * R['a'].fillna(0.0)).values, held.values, atol=1e-12)


def test_net_of_charges_turnover_and_borrow():
    """A flip (-1 -> +1) must be charged 2 x 6.4bps; shorts charged 0.5%/yr."""
    idx = pd.date_range('2020-01-01', periods=5, freq='B')
    W = pd.DataFrame({'a': [-1.0, 1.0, 1.0, 1.0, -1.0]}, index=idx)
    R = pd.DataFrame({'a': 0.0}, index=idx)  # isolate costs
    net, We, gross = C.net_of(W, R, vt=False)
    # We shifts decisions: dW = 1 (entry at t1), 2 (flip at t2); day-4 flip lands t5 (cut).
    exp = pd.Series([0.0, 1.0, 2.0, 0.0, 0.0], index=idx) * 6.4 / 1e4
    borrow = pd.Series([0.0, 1.0, 0.0, 0.0, 0.0], index=idx) * 0.005 / 252
    assert np.allclose(net.values[:4], (-exp - borrow).values[:4], atol=1e-15)
    assert net.iloc[4] == 0.0  # flip cost lands next day (T+1), past series end


def test_oas_book_smoke_and_flatten():
    """End-to-end on real data: net series exists, positive length, finite."""
    oas = C.load_series(f"{C.FRED}/hy_oas.csv")
    net, We, gross = C.oas_book(oas, win=63)
    assert len(net) > 500
    assert np.isfinite(net.values).all()
    assert We['a'].abs().max() <= 3.0 * 1.6 + 1e-9
