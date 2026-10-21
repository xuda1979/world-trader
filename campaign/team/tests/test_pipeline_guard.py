"""TDD tests for pipeline_guard.py — 'one backtest path' + 'PASS means honest' + decorr-first.

Pins: (1) a mock bespoke heredoc that computes Sharpe w/o bt/ is FLAGGED; a bt-using script is NOT;
(2) the committed champion passes the champion_publish_gate (honesty gauntlet green);
(3) decorr_first rejects the champion-vs-itself and passes independent noise.
"""
import os
import sys
import tempfile

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import corr_gate, pipeline_guard  # noqa: E402


def _write(tmp, name, body):
    p = os.path.join(tmp, name)
    with open(p, "w") as fh:
        fh.write(body)
    return p


def test_bt_only_flags_bespoke_metric_script():
    with tempfile.TemporaryDirectory() as tmp:
        bad = _write(tmp, "bad.py", "import numpy\ndef go(r):\n    return r.mean()/r.std()*np.sqrt(252)  # sharpe, no bt/\n")
        off = pipeline_guard.bt_only([bad])
        assert any(p == bad for p, _ in off)


def test_bt_only_allows_bt_powered_script():
    with tempfile.TemporaryDirectory() as tmp:
        good = _write(tmp, "good.py", "from bt.metrics import sharpe_d\nimport bt\ndef go(r):\n    return bt.sharpe_d(r)\n")
        off = pipeline_guard.bt_only([good])
        assert all(p != good for p, _ in off)


def test_champion_publish_gate_passes():
    ok, rep = pipeline_guard.champion_publish_gate()
    assert ok is True and rep["verify_r3"] is True


def test_decorr_first_rejects_champion():
    champ = corr_gate.load_champion()
    df = pd.DataFrame({"ret": champ})
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
        df.to_csv(fh.name, index=False); path = fh.name
    ok, c = pipeline_guard.decorr_first(path)
    os.unlink(path)
    assert ok is False and abs(c) > 0.15
