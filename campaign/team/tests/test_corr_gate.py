"""TDD tests for the decorrelation-first filter (corr_gate.py).

Verifies: (1) a candidate that IS the champion passes corr ~1.0 -> REJECT (decorr-first);
(2) a low/noise series decorrelates -> PASS; (3) fail-closed when candidate empty.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import corr_gate  # noqa: E402


def test_champion_is_rejected_decorr_first():
    champ = corr_gate.load_champion()
    ok, c = corr_gate.gate(champ)
    assert ok is False, "champion vs itself must NOT pass the blend-gate"
    assert abs(c) > 0.15


def test_independent_noise_passes():
    champ = corr_gate.load_champion()
    n = len(champ)
    noise = pd.Series(np.random.default_rng(0).normal(0, 1, n))
    ok, c = corr_gate.gate(noise)
    assert ok is True, f"independent noise should pass, corr={c}"


def test_fail_closed_empty_ref():
    ref = pd.read_csv(corr_gate.CHAMP)["ret"].dropna().astype(float).reset_index(drop=True)
    ok, c = corr_gate.gate(ref, corr_max=0.15)
    assert ok is False and c is not None  # ref==candidate -> corr=1 -> reject
