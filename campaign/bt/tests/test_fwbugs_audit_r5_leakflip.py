"""AUDIT_FWBUGS R5 - the GATES_CONTRACT_V2 section-12 Step-2 flip: RED-first test pair.

Contract section 12 step 5: move AUDIT_GATES2/r4/test_r4_leakflip_pair.py's four tests
into campaign/bt/tests/ (drop the [OLD] pin - its replacement IS the default-on
semantics). Charter precondition ("NO behavior change to bt/gates.py without a RED-first
test pair showing old-vs-new semantics on a fixture") is satisfied by running THIS file
RED-first: under old (opt-in) semantics the three [NEW] tests fail (no leak gate runs
without the kwarg -> KeyError), and the deleted pin
(test_fwbugs_audit_r3.py::test_gates_default_has_no_leak_gate) was the old-semantics
migration pin, removed in the same commit as the flip per the runbook.

RED evidence (2026-09-08 08:5x CST, default-OFF source, before the flip):
  3 failed (KeyError: 'leak_ok') / 1 passed - the [NEW] trio RED, exactly the contract's
  old-semantics outcome. After the flip: 4/4 GREEN (see AUDIT_FWBUGS FINDINGS.md).
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
import pandas as pd

from bt.gates import run

RNG = np.random.default_rng(11)


def _fixture():
    """n=800 drift returns + a lagged (causal T+1) position series + a same-day leak."""
    n = 800
    r = pd.Series(0.0004 + 0.01 * RNG.standard_normal(n),
                  index=pd.bdate_range("2020-01-01", periods=n))
    causal = r.shift(1).fillna(0.0).values          # position at t knows only r_{<t}
    leaky = r.values                                # position at t consumes r_t (THE defect)
    return r, causal, leaky


def test_r5_new_semantics_leaky_sig_rejected_by_default():
    """[NEW] A same-day-leak book fails the composite by DEFAULT, no opt-in kwarg."""
    r, _, leaky = _fixture()
    res = run(r, sig=leaky)                          # note: NO leak_check kwarg
    assert res["leak_ok"] is False, f"leak gate not on by default: {res.get('leak')}"
    assert res["pass"] is False
    assert res["leak"]["leak"] is True


def test_r5_new_semantics_causal_sig_passes_leak_by_default():
    """[NEW] An honest T+1 book is not spuriously flagged - default-on accepts causal
    positions (r.shift(1) has zero same-period correlation with r, so the materiality
    floor MIN_ABS_CORR=0.20 is not met and leak=False)."""
    r, causal, _ = _fixture()
    res = run(r, sig=causal)
    assert res["leak_ok"] is True, f"causal book flagged: {res.get('leak')}"


def test_r5_new_semantics_missing_sig_fails_closed_by_default():
    """[NEW] Default-on with no positions is unmeasurable -> leak_ok=False, composite
    False (fail-closed, the R2 rule now applied to the default path)."""
    r, _, _ = _fixture()
    res = run(r)                                     # no sig, no leak_check kwarg
    assert res["leak_ok"] is False
    assert res["pass"] is False
