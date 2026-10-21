"""ROUND 4 AUDIT regression (HUNT_CMDT2): campaign/scripts/cot_delta_weekly.py must build its
weekly book for ALL configs it advertises in __main__, including z_thr>0.

Current behaviour (bug, R4 audit finding): market_weekly(z_thr>0) does
    sig = np.where(...)          # line 60 -> numpy.ndarray
    ...
    pos_week = sig.shift(1)      # line 62 -> AttributeError on ndarray
which build_weekly swallows (`except Exception: nets[m]=None`, line 74-76), so
pd.DataFrame({m: None,...}) then raises ValueError("If using all scalar values...").
Net effect: 3 of the 4 __main__ configs cannot run at all.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")

import pandas as pd
import cot_delta_weekly as cdw


def test_market_weekly_survives_zthr_positive():
    n, to = cdw.market_weekly("gold", lookback=1, z_thr=0.5)
    assert isinstance(n, pd.Series) and len(n) > 300, "z_thr>0 path must return a weekly Series"


def test_build_weekly_survives_zthr_positive():
    df = cdw.build_weekly(1, 0.5)
    assert df is not None and df.shape[1] == 9, "all 9 markets must build, none swallowed to None"
