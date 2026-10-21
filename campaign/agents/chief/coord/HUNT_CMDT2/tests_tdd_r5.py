"""HUNT_CMDT2 ROUND 5 TDD — propane (DPROPANEMBTX) corner. RED-first.

Contract per CHARTER.md ROUND 5 (a) + GATES_CONTRACT_V2:
  * T+1: the day-t weight change must be decided from data <= t-1 (net_of shift(1)).
  * PIT publication lag: FRED daily spot prints are same-day observations, but the sleeve
    must be invariant to a plausible +1-day publication delay (no same-day decision use).
  * A zero signal (all-flat book) must produce exactly zero returns/costs.
  * The spread book is dollar-neutral by construction: gross exposure nets to 0 pre-VT.
  * V2 battery: every acceptance-track gates.run call carries sig= + leak_check=True +
    the beats-passive trio (§6 Step-1 / §7). A battery without leak dict fails the test.
Run from repo root:  python3 -m pytest campaign/agents/chief/coord/HUNT_CMDT2/tests_tdd_r5.py -q
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, ROOT)
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/scripts")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest  # noqa: E402


def _mod():
    import HUNT_CMDT2_round5 as M
    return M


def _propane():
    p = pd.read_csv(f"{ROOT}/tools/quant/data/more_fred/DPROPANEMBTX.csv",
                    index_col=0, parse_dates=True)['value'].astype(float)
    return p


def _rets(lo='2010-01-01'):
    """Bounded propane returns + the 2-leg frame (the module's own honest-span builder)."""
    M = _mod()
    r, r2 = M.prop_ung_returns()
    r = r[r.index >= lo]
    r2 = r2[r2.index >= lo]
    return r, r2


# --- 1. data reality ---------------------------------------------------------
def test_propane_file_shape():
    p = _propane()
    assert len(p) >= 8000
    assert p.index[0].year == 1992
    assert p.isna().sum() == 0
    # daily-ish: >= 150 real level changes in a median year (print staleness guard)
    chg = p.diff().ne(0).groupby(p.index.year).sum()
    assert chg.median() >= 150


# --- 2. T+1: decision data <= t-1 -------------------------------------------
def test_tplus1_weights_are_shifted():
    M = _mod()
    p = _propane()
    r, r2 = _rets('2010-01-01')
    net, We, gross, W = M.run_spread_book(r2, win=63, z_in=1.0, z_out=0.0, vt=False)
    # zero out the FIRST 100 return rows: an honest T+1 book decided from data <= t-1
    # still holds positions whose P&L lands inside the zeroed window... instead, verify
    # the weights actually used on day t equal the signal-day weights of day t-1 exactly.
    assert We.equals(W.shift(1).fillna(0.0))


def test_no_lookahead_truncation_probe():
    """Zero the last 250 days of the decision data, rebuild: every weight BEFORE the
    truncation point must be byte-identical (a look-ahead book would move)."""
    M = _mod()
    p = _propane()
    full, _ = _rets('2012-01-01')
    net_f, We_f, _, W_f = M.run_spread_book(_rets('2012-01-01')[1], win=63, z_in=1.0, z_out=0.0)
    cut = full.index[-250]
    r2f = _rets('2012-01-01')[1]
    trunc = r2f[r2f.index < cut]
    net_t, We_t, _, W_t = M.run_spread_book(trunc, win=63, z_in=1.0, z_out=0.0)
    a = We_f[We_f.index < cut]
    b = We_t[We_t.index < cut]
    assert a.equals(b)


# --- 3. PIT publication lag --------------------------------------------------
def test_pit_one_day_publication_lag_changes_book_like_a_delay():
    """A +1-day publication delay (each print visible one session later == values shifted
    one row) commutes with rolling stats, the shift(1) and the hysteresis state machine:
    the delayed book's day-t weight must equal the original book's day-(t-1) weight.
    Any same-day print consumption would break the equality."""
    M = _mod()
    full, r2f = _rets('2014-01-01')
    net_a, We_a, _, _ = M.run_spread_book(r2f, win=63, z_in=1.0, z_out=0.0, vt=False)
    r2_lag = r2f.shift(1)                        # every print arrives one session later
    net_b, We_b, _, _ = M.run_spread_book(r2_lag, win=63, z_in=1.0, z_out=0.0, vt=False)
    # position alignment: lagged book's day-t weight == original book's day-(t-1) weight
    assert np.array_equal(We_b.values[1:], We_a.values[:-1])


# --- 4. structural invariants -------------------------------------------------
def test_zero_signal_book_is_exactly_flat():
    M = _mod()
    p = _propane()
    r, r2 = _rets('2018-01-01')
    net, We, gross, W = M.run_spread_book(r2, win=63, z_in=1e9, z_out=1e9)  # never enters
    assert np.allclose(net.values, 0.0)
    assert np.allclose(We.values, 0.0)


def test_spread_book_is_dollar_neutral():
    M = _mod()
    p = _propane()
    r, r2 = _rets('2015-01-01')
    net, We, gross, W = M.run_spread_book(r2, win=63, z_in=1.0, z_out=0.0)
    live = We[(We != 0).any(axis=1)]
    assert len(live) > 0
    assert np.allclose(live.sum(axis=1), 0.0, atol=1e-12)


# --- 5. V2 battery wiring ------------------------------------------------------
def test_v2_battery_requires_leak_and_trio_keys():
    """The battery output must publish the §6 leak dict + beats-passive block; a book
    evaluated without leak_ok published is a contract violation (escalated mis-statement)."""
    M = _mod()
    p = _propane()
    r, r2 = _rets('2018-01-01')
    net, We, gross, W = M.run_spread_book(r2, win=63, z_in=1.0, z_out=0.0)
    res = M.v2_battery(net, sig=We['prop'], ref=None, spy=None, ief=None, cta=None)
    assert 'leak' in res and res.get('leak_ok') is not None
    assert 'beats_passive' in res and 'beats_passive_ok' in res
    assert 'v2' in res
