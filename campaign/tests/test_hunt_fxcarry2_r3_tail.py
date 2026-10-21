#!/usr/bin/env python3
"""TDD tests for HUNT_FXCARRY2 round-3 tail-control machinery.

Locks the evaluation-honesty properties the mechanisms must have before any
performance number from them is admissible:
  1. A stop that never breaches leaves the book byte-identical.
  2. Pre-breach history is preserved (a stop affects only the future).
  3. State transitions use only data <= t (no lookahead: perturbing future
     returns cannot change today's live/flat state).
  4. Crash-cap: a hit at day i zeroes exactly days i+1..i+halt, never the past,
     and never double-shifts (no i+2 start).
  5. Monthly loss-cap: a breaching month m scales exactly month m+1, leaves
     month m untouched.
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")

from scripts.HUNT_FXCARRY2_round3 import dd_stop, monthly_losscap, apply_cap_to_series


def _mk(rets, seed=0):
    idx = pd.bdate_range("2004-01-01", periods=len(rets))
    return pd.Series(rets, index=idx)


def test_never_breaching_stop_is_identity():
    r = _mk([0.001] * 300)          # steady gains -> dd never < -10%
    out, nstop = dd_stop(r, stop=-0.10)
    assert nstop == 0, f"expected 0 stopped days, got {nstop}"
    pd.testing.assert_series_equal(out, r)


def test_pre_breach_history_preserved():
    # flat, one -20% day at t=100, then recovery
    rets = [0.0] * 100 + [-0.20] + [0.0] * 200
    r = _mk(rets)
    out, nstop = dd_stop(r, stop=-0.10)
    # days before the breach must be untouched
    pd.testing.assert_series_equal(out.iloc[:100], r.iloc[:100])
    # the breach day itself is realized live (stop acts from t+1)
    assert out.iloc[100] == r.iloc[100]
    assert nstop > 0


def test_no_lookahead_in_state():
    # change ONLY future returns; live/flat state up to t must not move
    rets = [0.0005] * 100 + [-0.05] * 50 + [0.001] * 150
    r1 = _mk(rets)
    r2 = r1.copy()
    r2.iloc[200:] = -0.01           # future divergence
    o1, _ = dd_stop(r1, stop=-0.10)
    o2, _ = dd_stop(r2, stop=-0.10)
    # decisions up to index 150 are identical (state at t uses data <= t)
    # (allow the tail to differ)
    pd.testing.assert_series_equal(o1.iloc[:150], o2.iloc[:150])


def test_crash_cap_window_exact():
    rets = [0.0] * 50 + [-0.03] + [0.001] * 100
    r = _mk(rets)
    out = apply_cap_to_series(r, crash=-0.02, halt=10)
    assert out.iloc[50] == r.iloc[50]                    # hit day realized
    assert (out.iloc[51:61] == 0).all(), "days i+1..i+halt must be flat"
    assert (out.iloc[61:] != 0).all(), "trading must resume at i+halt+1"
    pd.testing.assert_series_equal(out.iloc[:51], r.iloc[:51])  # past intact


def test_crash_cap_no_double_shift():
    # single hit must cost exactly `halt` flat days, not halt+1
    rets = [0.0] * 30 + [-0.05] + [0.02] * 40
    r = _mk(rets)
    out = apply_cap_to_series(r, crash=-0.02, halt=10)
    nflat = int((out.iloc[31:] == 0).sum())
    assert nflat == 10, f"expected exactly 10 flat days, got {nflat}"


def test_monthly_losscap_scales_next_month_only():
    # real calendar: Jan-2004 has 22 bdays; use the period boundary itself
    idx = pd.bdate_range("2004-01-01", periods=30)   # 22 in Jan, 8 in Feb
    cut = int((idx < "2004-02-01").sum())            # 22
    assert idx[cut - 1].month == 1 and idx[cut].month == 2
    r = pd.Series(0.0, index=idx)
    r.iloc[:cut] = -0.04 / cut                       # Jan = -4% (breaches -3%)
    r.iloc[cut:] = 0.001
    out, ndele = monthly_losscap(r, cap=-0.03, halve=0.5)
    pd.testing.assert_series_equal(out.iloc[:cut], r.iloc[:cut])  # Jan untouched
    assert np.allclose(out.iloc[cut:].values, (r.iloc[cut:] * 0.5).values)
    assert ndele == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"{len(fns) - failed}/{len(fns)} green")
    sys.exit(1 if failed else 0)
