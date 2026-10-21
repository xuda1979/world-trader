"""TDD RED->GREEN for HUNT_VXV_TERM overlay composition on campaign/bt.
Properties under test (exact, no approx):
  P1 constant m=1 reproduces champion except day0 entry cost 6.4bps*gross.
  P2 exact cost stream: costs_t = |m_t - m_{t-1}| * 6.4bps * gross (m_{-1}=0).
  P3 T+1 composition: overlay_ret consumes EXECUTED m (caller shifts via bt.lag_signal);
     a signal spike at t must not change ret'_t, only ret'_{t+1}.
"""
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')

from overlay import overlay_ret  # RED: module does not exist yet
from bt.engine import lag_signal


def test_p1_constant_one_reproduces_champion():
    idx = pd.date_range('2020-01-01', periods=5, freq='B')
    r = pd.Series([0.001, -0.002, 0.003, 0.0005, 0.002], index=idx)
    m = pd.Series(1.0, index=idx)
    out = overlay_ret(r, m, gross=1.0)
    # day0: r*m - 6.4bps*1 (entry 0->1); days1..: exact champion
    assert abs(out.iloc[0] - (r.iloc[0] - 6.4e-4)) < 1e-15
    assert np.allclose(out.iloc[1:].values, r.iloc[1:].values, atol=1e-15)


def test_p2_exact_cost_stream():
    idx = pd.date_range('2020-01-01', periods=4, freq='B')
    r = pd.Series([0.01, 0.01, 0.01, 0.01], index=idx)
    m = pd.Series([0.0, 1.0, 1.0, 0.0], index=idx)
    out = overlay_ret(r, m, gross=3.367)
    exp_cost = np.array([0.0, 1.0, 0.0, 1.0]) * 6.4e-4 * 3.367
    exp = r.values * m.values - exp_cost
    assert np.allclose(out.values, exp, atol=1e-15)


def test_p3_tplus1_no_same_day_leak():
    idx = pd.date_range('2020-01-01', periods=6, freq='B')
    r = pd.Series([0.01] * 6, index=idx)
    s = pd.Series(1.0, index=idx)          # always-on target...
    s.iloc[3] = 0.0                         # ...except a spike-off at t=3
    m_exec = lag_signal(s).fillna(0.0)      # executed m: off at t=4, not t=3
    out = overlay_ret(r, m_exec, gross=1.0)
    assert abs(out.iloc[3] - 0.01) < 1e-15            # t=3 UNCHANGED (no leak)
    assert abs(out.iloc[4] - (0.0 - 6.4e-4)) < 1e-15  # t=4 FLAT (m=0) + flip cost
    assert abs(out.iloc[5] - (0.01 - 6.4e-4)) < 1e-15 # t=5 back ON (re-entry cost)
