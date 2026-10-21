"""AUDIT_GATES2 R4 — RED-FIRST TEST PAIR for the leak_check DEFAULT-ON flip.

Charter precondition: "NO behavior change to bt/gates.py without a RED-first test pair
showing old-vs-new semantics on a fixture." This file IS that pair. bt/gates.py is NOT
modified by this round; the GREEN side of the pair is demonstrated by running pytest with
the semantics-identical shadow plugin (leak_default_shadow_plugin.py), which patches
run() to leak_check=True when the caller did not pass it — exactly what the ratified flip
would do in source.

Old (current, v2-draft) semantics: leak gate is opt-in (leak_check=True); without it the
result dict has no leak keys and pass ignores lookahead entirely.
New (proposed) semantics: leak gate is DEFAULT-ON; fail-closed when sig is absent;
leak_check=False explicitly restores measurement-only semantics and must be disclosed.

Tests marked [NEW] are RED under old semantics and GREEN under the flip.
The test marked [OLD] is the migration pin: GREEN under old, FAILS under the flip, and is
DELETED/REPLACED at flip time (that replacement is part of the flip's test migration).

Run (from repo root):
  python3 -m pytest campaign/agents/chief/coord/AUDIT_GATES2/r4/test_r4_leakflip_pair.py -q            # old semantics
  python3 -m pytest campaign/agents/chief/coord/AUDIT_GATES2/r4/test_r4_leakflip_pair.py -q \
      -p campaign.agents.chief.coord.AUDIT_GATES2.r4.leak_default_shadow_plugin                        # new semantics
"""
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), *[os.pardir] * 5))
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


def test_r4_new_semantics_leaky_sig_rejected_by_default():
    """[NEW] RED under old semantics (KeyError: no leak gate in result), GREEN under flip:
    a same-day-leak book fails the composite by DEFAULT, no opt-in needed."""
    r, _, leaky = _fixture()
    res = run(r, sig=leaky)                          # note: NO leak_check kwarg
    assert res["leak_ok"] is False, f"leak gate not on by default: {res.get('leak')}"
    assert res["pass"] is False
    assert res["leak"]["leak"] is True


def test_r4_new_semantics_causal_sig_passes_leak_by_default():
    """[NEW] RED under old semantics (KeyError), GREEN under flip: an honest T+1 book is
    not spuriously flagged — the default-on gate accepts causal positions."""
    r, causal, _ = _fixture()
    res = run(r, sig=causal)
    assert res["leak_ok"] is True, f"causal book flagged: {res.get('leak')}"


def test_r4_new_semantics_missing_sig_fails_closed_by_default():
    """[NEW] RED under old semantics (KeyError), GREEN under flip: default-on with no
    positions is unmeasurable -> leak_ok=False, composite False (fail-closed, R2 rule)."""
    r, _, _ = _fixture()
    res = run(r)                                     # no sig, no leak_check kwarg
    assert res["leak_ok"] is False
    assert res["pass"] is False


# (test_r4_old_semantics_pins_default_off REMOVED at flip time: the [OLD] default-OFF pin was
#  replaced by the three [NEW] tests above. flip commit 539f50e shipped leak_check default ON
#  per GATES_CONTRACT_V2 section-12 Step-2, so the OLD pin was stale and correct to drop.)
