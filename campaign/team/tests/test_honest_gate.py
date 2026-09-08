"""TDD test for the automatic honest-verification CI gate (honest_gate.py).

Asserts the committed champion passes BOTH the verify_r3 gauntlet AND the flatten sweep
(i.e., every sleeve input has ac1<0.5 and uniqR>=0.08 — the XGB1y-class artifact is gone).
This is the regression pin that makes a future bad 'record' fail closed before it is quoted.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import honest_gate  # noqa: E402


def test_committed_champion_is_honest():
    ok, rep = honest_gate.honest_verify()
    assert rep["verify_r3"] is True, rep["errors"][:500]
    assert rep["flat_ok"] is True
    assert ok is True


def test_every_sleeve_meets_flatten_floor():
    _, rep = honest_gate.honest_verify()
    for name, v in rep["flatten"].items():
        assert v["uniqR"] >= 0.08, f"{name} uniqR {v['uniqR']} < 0.08 (flatten trap)"
        assert v["ac1"] < 0.5, f"{name} ac1 {v['ac1']} >= 0.5"
