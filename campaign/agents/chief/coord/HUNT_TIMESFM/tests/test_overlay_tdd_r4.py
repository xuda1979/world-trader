"""TDD: constant-scale overlay on champion must be ~SR-neutral (SR is scale-invariant).
Prior convention (HUNT_CREDIT2 C-controls): net_g = champ * g, extra cost = |d(1.6*g)|
* 6.4bps only. Re-charging margin on (w-1) double-counts champion financing (bug)."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/chief/coord/HUNT_TIMESFM/work_r4")
from bt import metrics


def overlay_net_fixed(scale_held: pd.Series, champ: pd.Series, gear=1.6, cost=6.4e-4):
    s = scale_held.reindex(champ.index)
    w = s * gear
    to_extra = w.diff().abs().fillna(w.abs())
    return champ * s - to_extra * cost


def test_constant_scale_sr_neutral():
    idx = pd.bdate_range("2015-01-01", periods=2000)
    rng = np.random.default_rng(7)
    r = pd.Series(rng.normal(0.0004, 0.0063, len(idx)), index=idx)  # champ-like
    const = pd.Series(0.993, index=idx)
    net = overlay_net_fixed(const, r)
    assert abs(metrics.sharpe_d(net) - metrics.sharpe_d(r)) < 0.02


def test_step_mask_charges_transitions_only():
    idx = pd.bdate_range("2015-01-01", periods=10)
    r = pd.Series(0.0, index=idx)
    s = pd.Series(1.0, index=idx); s.iloc[5:] = 0.7
    net = overlay_net_fixed(s, r)
    assert abs(net.sum() + (1.6 + 0.48) * 6.4e-4) < 1e-12
