"""TDD RED->GREEN tests for RES_BASIS hunt R1 helpers (charter: campaign/team/charters/RES_BASIS.md).

Convention follows HUNT_CREDIT2_round5 (GATES_CONTRACT_V2 §0): gates.run(r=per-unit,
sig=effective weight) — sig*r must equal the held gross book (pre-cost).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_BASIS")

import numpy as np
import pandas as pd
import pytest

# determinism fix (AUDIT_DAX 2026-09-17): `import hunt_r1` collides on sys.modules with
# campaign/team/agents/RES_STATARB/test_hunt_r1.py. Load THIS hunt's hunt_r1.py under a
# unique alias so the selected module never depends on pytest collection order.
import os as _os, importlib.util as _ilu
_basis_dir = "/Users/daxu/software/world-trader/campaign/team/agents/RES_BASIS"
_spec = _ilu.spec_from_file_location("res_basis_hunt_r1", _os.path.join(_basis_dir, "hunt_r1.py"))
H = _ilu.module_from_spec(_spec); _spec.loader.exec_module(H)


def test_hysteresis_stays_flat_until_z_in():
    z = pd.Series([0.0, 1.9, 0.0, -1.9, 0.0])
    st = H.hysteresis_state(z, z_in=2.0, z_out=0.5)
    assert (st == 0.0).all()


def test_hysteresis_enters_and_holds_then_exits():
    z = pd.Series([0.0, 2.5, 1.5, 0.9, 0.4, 0.2, -2.5, -1.0, 0.0])
    st = H.hysteresis_state(z, z_in=2.0, z_out=0.5)
    assert list(st) == [0.0, 1.0, 1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0]


def test_hysteresis_nan_z_holds_state_and_never_enters():
    z = pd.Series([0.0, np.nan, 2.5, np.nan, 0.2])
    st = H.hysteresis_state(z, z_in=2.0, z_out=0.5)
    assert list(st) == [0.0, 0.0, 1.0, 1.0, 0.0]


def test_zscore_uses_only_past_values():
    """Day-(t-1) z must be invariant to day-t price: no FUTURE info in any decision."""
    px = pd.Series(np.linspace(100, 110, 60))
    z1 = H.zscore_trailing(px, win=20)
    px2 = px.copy(); px2.iloc[-1] += 50.0
    z2 = H.zscore_trailing(px2, win=20)
    assert abs(z1.iloc[-2] - z2.iloc[-2]) < 1e-12


def test_weekly_to_daily_pub_safe_lags():
    """Obs dated v is visible from v+lag only; earlier days carry NaN (never backward-fill
    an unpublished obs)."""
    wk = pd.Series([1.0, 2.0], index=pd.DatetimeIndex(['2020-01-01', '2020-01-08']))
    d = H.weekly_pub_safe(wk, lag_days=7, end='2020-01-15')
    assert pd.isna(d.loc['2020-01-07'])    # nothing published yet (01-01 obs visible 01-08)
    assert d.loc['2020-01-08'] == 1.0      # first visible day of the 01-01 obs
    assert d.loc['2020-01-14'] == 1.0      # 01-08 obs visible only from 01-15
    assert d.loc['2020-01-15'] == 2.0


def test_pair_book_dollar_neutral():
    r_a = pd.Series(0.01, index=pd.date_range('2020-01-01', periods=5))
    r_b = pd.Series(-0.005, index=pd.date_range('2020-01-01', periods=5))
    net, We, gross_r = H.pair_book(r_a, r_b, spread=np.log(1 + r_a) - np.log(1 + r_b),
                                   win=2, z_in=2.0, z_out=0.5, vt=False)
    assert (We.sum(axis=1).abs() < 1e-12).all()


def test_book_convention_sig_times_rpu_equals_gross():
    """Per-unit spread return x effective leg weight == gross book P&L (V2 §0 convention)."""
    idx = pd.date_range('2020-01-01', periods=30)
    r_a = pd.Series(np.random.default_rng(1).normal(0, .01, 30), index=idx)
    r_b = pd.Series(np.random.default_rng(2).normal(0, .01, 30), index=idx)
    sp = np.log((1 + r_a).cumprod() / (1 + r_b).cumprod())
    net, We, gross_r, rpu = H.pair_book(r_a, r_b, spread=sp, win=10, z_in=1.0, z_out=0.0,
                                        vt=False, return_rpu=True)
    gross = (We['a'] * r_a.reindex(We.index).fillna(0)
             + We['b'] * r_b.reindex(We.index).fillna(0))
    book = (rpu * We['a']).reindex(gross.index).fillna(0)
    assert np.allclose(book, gross, atol=1e-12)
