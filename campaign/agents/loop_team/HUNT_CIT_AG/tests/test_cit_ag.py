"""TDD tests for CIT-ags engine. RED before cit_ag.py exists."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))

def test_module():
    import cit_ag  # noqa

def test_cit_zscore_no_lookahead():
    import pandas as pd, numpy as np
    import cit_ag
    s = pd.Series(np.random.RandomState(0).normal(0, 1, 300).cumsum())
    z1 = cit_ag.zscore_26w(s)
    s2 = s.copy(); s2.iloc[299] = 1e6
    z2 = cit_ag.zscore_26w(s2)
    assert (z1.iloc[:250].fillna(0) == z2.iloc[:250].fillna(0)).all()

def test_cot_lag3():
    import pandas as pd
    import cit_ag
    s = pd.Series([1.0, 2.0, 3.0], index=pd.DatetimeIndex(["2020-01-05", "2020-01-06", "2020-01-07"]))
    out = cit_ag.cot_lag(s, days=3)
    assert list(out.index) == list(pd.DatetimeIndex(["2020-01-08", "2020-01-09", "2020-01-10"]))
    assert list(out.values) == [1.0, 2.0, 3.0]   # values preserved, dates shifted

def test_signal_long_short():
    import pandas as pd, numpy as np
    import cit_ag
    s = pd.Series(np.r_[np.zeros(30), 3.0, -3.0])
    sig = cit_ag.cit_signal(s, entry=1.5, exit_z=0.5)
    assert sig.iloc[29] == 0.0                 # before spike: flat
    assert sig.iloc[30] == 1.0                 # spike row: long entry
    assert sig.iloc[31] == 0.0                 # z collapses through exit: flat (no same-row flip)

def test_engine_smoke():
    import pandas as pd, numpy as np
    import cit_ag
    idx = pd.bdate_range("2015-01-01", periods=800)
    px = pd.Series(np.cumprod(1 + np.random.RandomState(1).normal(0.0002, 0.01, 800)), index=idx)
    cot_idx = pd.date_range("2015-01-01", periods=200, freq="W-TUE")
    cot_idx = cot_idx[cot_idx <= idx[-1]]
    cot = pd.Series(np.random.RandomState(2).normal(0, 1, len(cot_idx)), index=cot_idx)
    net = cit_ag.run_sleeve(cot, px)
    assert len(net) > 300 and net.abs().max() < 0.2
