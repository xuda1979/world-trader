"""TDD RED tests for RES_META cross-asset engine library (meta_lib.py).

Contract under test (campaign/bt honesty + charter gates):
  m1. load_px: fail-closed loader -> float close series, deduped, sorted, no NaN.
  m2. rets: pct_change dropna, index DatetimeIndex.
  m3. universe(): >=10 tradeable legs, ALL real ETF/FX closes on disk (no VIX spot).
  m4. reversal_positions: ranks past L-day returns, long worst / short best,
      T+1-safe (uses ONLY data up to t), positions in [-1,1], dollar-neutral.
  m5. reversal_positions shift-safe: positions at t are a function of returns
      strictly before t (perturb r[t] -> positions[t] unchanged).
  m6. clip_rets: |r|<=cap enforced; NaN stays NaN.
  m7. sleeve_net: returns a net Series net of 6.4bps full |dW| + borrow + margin
      via bt.engine primitives (no bespoke cost heredoc).
  m8. vol_norm: trailing-only expanding vol scale (no lookahead; perturbation test).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
sys.path.insert(0, f"{ROOT}/campaign/team/agents/RES_META")

import meta_lib as ML


def test_m1_load_px_real_file():
    s = ML.load_px("UUP")
    assert isinstance(s.index, pd.DatetimeIndex)
    assert s.notna().all() and len(s) > 4000
    assert (s > 0).all()


def test_m1b_load_px_missing_fails():
    with pytest.raises(FileNotFoundError):
        ML.load_px("NOPE_XYZ")


def test_m2_rets():
    s = ML.load_px("UUP")
    r = ML.rets(s)
    assert len(r) == len(s) - 1 or len(r) == len(s)
    assert isinstance(r.index, pd.DatetimeIndex)


def test_m3_universe_tradeable_no_vix():
    u = ML.universe()
    assert len(u) >= 10
    assert "VIX" not in " ".join(u).upper() and "VIXY" not in " ".join(u).upper()
    for leg in u:
        ML.load_px(leg)  # every leg must exist on disk


def test_m4_reversal_positions_shape():
    rng = np.random.default_rng(7)
    R = pd.DataFrame(rng.normal(0, 0.01, (300, 4)),
                     index=pd.date_range("2020-01-01", periods=300, freq="B"),
                     columns=list("abcd"))
    P = ML.reversal_positions(R, L=8, n_leg=1)
    assert P.shape == R.shape
    body = P.iloc[20:].dropna(how="all")
    assert len(body) > 250
    assert (P.abs() <= 1.0 + 1e-12).all().all()
    # dollar-neutral: every row sums to ~0
    s = P.sum(axis=1).dropna()
    assert (s.abs() < 1e-9).all()


def test_m5_reversal_positions_no_lookahead():
    rng = np.random.default_rng(8)
    R = pd.DataFrame(rng.normal(0, 0.01, (200, 4)),
                     index=pd.date_range("2020-01-01", periods=200, freq="B"),
                     columns=list("wxyz"))
    P = ML.reversal_positions(R, L=8, n_leg=1)
    R2 = R.copy()
    R2.iloc[150] = R2.iloc[150] * 10.0     # shock TODAY
    P2 = ML.reversal_positions(R2, L=8, n_leg=1)
    # positions on the SAME day must be unchanged (T+1: decide on past only)
    pd.testing.assert_frame_equal(P.iloc[:151], P2.iloc[:151])


def test_m6_clip_rets():
    rng = np.random.default_rng(9)
    r = pd.Series(rng.normal(0, 0.01, 100))
    r.iloc[0] = np.nan          # pct_change head shape
    r.iloc[50] = -0.9
    c = ML.clip_rets(r, cap=0.18)
    assert c.abs().max() <= 0.18 + 1e-12
    assert np.isnan(c.iloc[0])   # NaN stays NaN


def test_m7_sleeve_net_uses_engine_costs():
    rng = np.random.default_rng(10)
    idx = pd.date_range("2020-01-01", periods=400, freq="B")
    P = pd.DataFrame(rng.choice([-1.0, 0.0, 1.0], (400, 2)), index=idx, columns=["a", "b"])
    R = pd.DataFrame(rng.normal(0, 0.01, (400, 2)), index=idx, columns=["a", "b"])
    net = ML.sleeve_net(P, R)
    assert isinstance(net, pd.Series) and len(net) > 300
    # gross book must be the P*R sum (engine arithmetic), costs subtracted,
    # 1.6x day-level leverage cap applied first (campaign honesty contract)
    from bt.engine import cost_turnover, margin_cost, cap_leverage
    w = cap_leverage(P.shift(1).fillna(0.0), 1.6)
    gross = (w * R.fillna(0.0)).sum(axis=1)
    manual = (gross - cost_turnover(w, 6.4)
              - ML.borrow_cost(w)
              - margin_cost(w.abs().sum(axis=1))).dropna()
    pd.testing.assert_series_equal(net, manual, check_names=False)


def test_m8_vol_norm_trailing_only():
    rng = np.random.default_rng(11)
    r = pd.Series(rng.normal(0, 0.01, 300))
    s = ML.vol_norm_scale(r)
    assert len(s) == len(r)
    r2 = r.copy(); r2.iloc[200] *= 5
    s2 = ML.vol_norm_scale(r2)
    assert (s.iloc[:200] == s2.iloc[:200]).all()   # today's r must not scale today
