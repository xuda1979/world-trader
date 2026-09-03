"""RED check: verify the LONG-ONLY clamp test actually fails on an L/S builder
(negative control proving the test has teeth)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))))
import numpy as np, pandas as pd
from test_crypto_longonly import _series, tsmom_sig


def test_red_control_ls_builder_fails_longonly_gate():
    # an L/S builder MUST fail the long-only property (teeth check)
    px = _series()
    r = px.pct_change().fillna(0.0)
    sig = tsmom_sig(px, 21).fillna(0.0)   # includes -1 legs (no clamp)
    from bt import engine as E
    scale = E.vol_target_scale(r.to_frame('r'), target=0.10, window=60, cap=3.0)
    w = (sig * scale['r']).fillna(0.0)
    assert (w < 0).any(), "control weak: no negative positions generated"
