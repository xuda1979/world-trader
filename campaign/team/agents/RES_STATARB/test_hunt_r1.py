"""TDD tests for RES_STATARB hunt_r1 (RED first: hunt_r1.py did not exist)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_STATARB")
import numpy as np, pandas as pd
import pytest
import bt.engine as eng
# determinism fix (AUDIT_DAX 2026-09-17): `import hunt_r1` collides on sys.modules with
# campaign/team/tests/test_res_basis_r1.py (both name their module `hunt_r1`; whichever
# imports first wins). Load THIS directory's hunt_r1.py under a unique alias so the
# selected module never depends on pytest collection order.
import os as _os, importlib.util as _ilu
_statarb_dir = _os.path.dirname(_os.path.abspath(__file__))
_spec = _ilu.spec_from_file_location("statarb_hunt_r1", _os.path.join(_statarb_dir, "hunt_r1.py"))
H = _ilu.module_from_spec(_spec); _spec.loader.exec_module(H)


def test_t1_positions_lag_returns():
    """T+1: day-150 POSITIONS must not depend on day-150 returns; day-151 must."""
    idx = pd.bdate_range('2020-01-01', periods=300)
    rng = np.random.default_rng(7)
    R = pd.DataFrame(rng.normal(0, 0.01, (300, 6)), index=idx,
                     columns=[f'I{i}' for i in range(6)])
    p = '/tmp/statarb_test_panel.csv'
    (R * 100).to_csv(p)
    _, _, We1 = H.build(p, 'mom', 21, 2)
    R2 = R.copy(); R2.iloc[150] = -R2.iloc[150]
    (R2 * 100).to_csv(p)
    _, _, We2 = H.build(p, 'mom', 21, 2)
    t0, t1 = idx[150], idx[151]
    assert np.allclose(We1.loc[t0], We2.loc[t0])       # decided at close 149
    assert not np.allclose(We1.loc[t1], We2.loc[t1])   # reacts at t+1


def test_weights_dollar_neutral():
    idx = pd.bdate_range('2020-01-01', periods=120)
    R = pd.DataFrame(0.001, index=idx, columns=[f'I{i}' for i in range(8)])
    tr = R.rolling(21).mean()
    W = H.ls_weights(R, tr, 2)
    live = W.iloc[21:]  # trailing signal is valid from tr's first non-NaN row (index 20);
                        # T+1 (shift(1) in gross_book) trades it from index 21 onward
    assert ((live > 0).sum(axis=1) == 2).all() and ((live < 0).sum(axis=1) == 2).all()
    # NaN signal window: rolling(21) yields its first valid mean at index 20, so only the
    # first 20 rows are signal-less and must stay flat (never enters). Prior `iloc[:21]`
    # was an off-by-one that wrongly demanded the first valid-signal row be flat too.
    assert W.iloc[:20].abs().sum().sum() == 0
    # T+1 warmup rows are deliberately zero (asserted above) and build() truncates them out
    # of the live book, so the +/-1-unit side checks apply to the live span (AUDIT_DAX:
    # previously asserted over the whole frame incl. warmup, contradicting the flat check).
    assert np.allclose(live[live > 0].fillna(0).sum(axis=1), 1.0)  # long side = 1 unit
    assert np.allclose(live[live < 0].fillna(0).sum(axis=1), -1.0)  # short side = -1 unit


def test_cost_charge_full_dw():
    """Flip 1 -> -1 must charge |dW|=2 at 6.4bps (full one-side notional convention)."""
    idx = pd.bdate_range('2020-01-01', periods=5)
    W = pd.DataFrame({'a': [0.0, 1.0, 1.0, -1.0, 0.0]}, index=idx)
    c = eng.cost_turnover(W, cost_bps=6.4)
    assert abs(c.iloc[1] - 6.4e-4) < 1e-12
    assert abs(c.iloc[3] - 2 * 6.4e-4) < 1e-12


def test_net_subtracts_costs_and_borrow():
    idx = pd.bdate_range('2020-01-01', periods=60)
    rpu = pd.Series(0.0, index=idx)
    We = pd.DataFrame(-1.0, index=idx, columns=['I0'])  # short 1 unit
    net = H.net_of(rpu, We)
    assert abs(net.iloc[1] + 0.005 / 252) < 1e-12  # borrow 0.5%/yr on 1 short unit
    assert net.iloc[0] < -6e-4  # day-1 establishment cost charged (full |dW|)
